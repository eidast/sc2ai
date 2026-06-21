## Context

El proyecto tiene 4 perfiles de estrategia YAML (`standard_macro`, `stargate_open`, `robo_open`, `fast_expand`) cada uno con sesgos iniciales, ajustes de scouting, y fórmulas de prioridad distintas. El modo `ml_shadow` existe como concepto pero no produce predicciones — `_last_shadow_prediction` es `None` siempre. El motor heurístico (`BiasCalculator` + `PriorityEngine`) ya evalúa un perfil activo por step y registra la acción recomendada en `utility.recommended_action`.

También hay un bug: `BiasCalculator._apply_scout_decay()` muta el dict `scout_metadata` in-place. Con múltiples calculadoras, se aplicaría decay N veces sobre los mismos datos.

## Goals / Non-Goals

**Goals:**
- Activar predicciones reales en `ml_shadow` usando perfiles YAML existentes
- Soportar 1+ shadow profiles simultáneos
- Cada shadow tiene su propio `BiasCalculator` + `PriorityEngine` independiente
- Shadow predictions se registran en `decisions.jsonl` sin afectar gameplay
- Eliminar el bug de doble decay en `BiasCalculator`
- Validación CLI: error si `ml_shadow` sin `--shadow-profile`

**Non-Goals:**
- ML real (modelos entrenados)
- Ejecutar acciones shadow (solo predicción)
- Cambiar el comportamiento de `heuristic` mode
- Migrar a otra librería CLI (argparse es suficiente)

## Decisions

### 1. Arquitectura: arrays de engines en vez de un solo shadow

**Decisión**: `self._shadow_bias_calculators: list[BiasCalculator]`, `self._shadow_priority_engines: list[PriorityEngine]`, `self._shadow_profiles: list[str]`, `self._last_shadow_predictions: list[dict]`.

**Alternativa considerada**: Un solo shadow. Rechazada porque el usuario quiere comparar múltiples estrategias en un mismo juego para A/B testing más rico.

**Racional**: Arrays de engines independientes. Cada uno recibe los mismos `features` pero evalúa con su propio `BiasCalculator` (sesgos distintos) y `PriorityEngine` (fórmulas distintas). El overhead es negligible — son evaluaciones de fórmulas aritméticas, no inferencia de ML.

### 2. Formato del shadow_prediction

**Decisión**: `shadow_predictions` (plural, array) reemplaza `shadow_prediction` (singular). Cada entrada:

```json
{
  "profile": "stargate_open",
  "recommended_action": {"type": "BUILD_UNIT", "target": "VOIDRAY", "score": 0.92}
}
```

**Alternativa considerada**: Mantener `shadow_prediction` singular con el primer shadow. Rechazada porque no escala a múltiples y rompe la semántica del array.

**Racional**: Reusa `_serialize_action()` para consistencia con `utility.recommended_action`. El campo `profile` identifica qué estrategia produjo la predicción.

### 3. Fix del scout decay

**Decisión**: Eliminar `BiasCalculator._apply_scout_decay()`. El decay ya lo aplica `ScoutMetadata.apply_decay()` en `on_step:142`. El `BiasCalculator` recibe los metadatos ya procesados vía `scout_metadata.to_dict()`.

**Alternativa considerada**: Pasar una copia del dict a cada `BiasCalculator`. Rechazada porque no arregla la causa raíz (responsabilidad duplicada).

**Racional**: Un solo punto de decay = comportamiento predecible. `ScoutMetadata` es dueño del estado de scouting; `BiasCalculator` es consumidor.

### 4. Validación CLI

**Decisión**: `--shadow-profile` usa `action="append"`. Si `--policy-mode ml_shadow` y `len(shadow_profiles) == 0`, error con lista de perfiles disponibles.

**Alternativa considerada**: `nargs="*"`. Rechazada porque `action="append"` es más explícito y estándar para flags repetibles.

**Racional**: Error temprano con mensaje útil. El usuario sabe exactamente qué perfiles existen.

### 5. Initialize-on-first-use para los shadow engines

**Decisión**: Los shadow `BiasCalculator` y `PriorityEngine` se crean en `__init__` si estamos en `ml_shadow` mode, igual que el engine activo se crea en `on_step` (línea 251). Mantener el patrón lazy init para consistencia, pero para shadows es en `__init__` porque ya sabemos el perfil de antemano.

**Alternativa considerada**: Crearlos lazy en `on_step`. Rechazada porque el perfil shadow se conoce en construcción, no hay razón para diferirlo.

## Risks / Trade-offs

- **[Breaking] Cambio de `shadow_prediction` → `shadow_predictions`**: Herramientas que lean `decisions.jsonl` esperando el campo singular se romperán. → Mitigación: no hay consumidores downstream todavía; es el momento correcto para hacer el cambio.
- **[Perf] N engines evaluando por step**: Con 3 shadows, son 4 evaluaciones de `PriorityEngine` por step (~22 steps/segundo en fast mode). → Mitigación: son evaluaciones de fórmulas aritméticas, no inference. Overhead estimado <1ms por step.
- **[Estado] BiasCalculator recibe dict compartido**: `scout_metadata.to_dict()` devuelve un dict nuevo, así que las calculadoras no comparten referencia. Ya verificado.
