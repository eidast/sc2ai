## Context

El bot actual (`MyBot` en `src/bot/core.py`) ejecuta cada step una secuencia fija de llamadas `manage_*` que deciden autónomamente qué hacer basadas en reglas hardcodeadas. El sistema de decisión (`src/bot/decision.py`) es una FSM con 5 estados discretos (DEFEND/ATTACK/RECOVER/SURRENDER/WON) que transicionan por umbrales numéricos. No existe un contexto estratégico compartido entre los distintos subsistemas.

El pipeline de observación (`src/ml/observation.py`) ya extrae ~50 features por step (composición enemiga, threat assessment, counters, métricas de army/eco). Esta información está disponible pero solo se usa para logging, reportes y los thresholds del FSM — no para guiar decisiones de build/producción en tiempo real.

El enfoque de "utility-based AI" es el estándar en la industria de videojuegos para NPCs adaptativos (The Sims, Civilization, F.E.A.R., Halo 3). Consiste en: cada acción posible tiene una curva de utilidad que se evalúa cada frame; gana la de mayor score. Es inherentemente continuo y no requiere árboles de decisión ni estados discretos.

## Goals / Non-Goals

**Goals:**
- Reemplazar el sistema de decisión monolítico por un engine basado en utility scoring con biases continuos
- Permitir que el scouting enemigo sea el driver principal de las decisiones tácticas, ponderado por certeza y antigüedad
- Definir estrategias como datos (YAML) separados del código de ejecución
- Hacer que los `manage_*` consulten al engine en lugar de decidir autónomamente
- Preparar la arquitectura para que un modelo ML entrene parámetros sin tocar la lógica de ejecución
- Soportar múltiples razas (Protoss hoy, Terran/Zerg futuro) sin cambios de código

**Non-Goals:**
- No implementar ML/red neuronal en este cambio (solo preparar la arquitectura)
- No modificar la ejecución del "cómo" (pathfinding, micro, placement, defensa reactiva)
- No implementar perfiles para Terran/Zerg (solo la arquitectura y perfiles Protoss)
- No reemplazar el sistema de logging/reportes/eventos existente
- No modificar el script de lanzamiento (`scripts/run.py`) ni la CLI

## Decisions

### D1: Utility-Based AI en lugar de sistema experto con árboles de decisión

**Decisión**: Usar un `PriorityEngine` que evalúa utilidad de N acciones cada step y ejecuta la mejor.

**Alternativas consideradas:**
- **Árbol de decisión (if-else jerárquico)**: Lo que tiene el bot hoy. Rígido, no escala a multi-raza, no maneja incertidumbre de scouting.
- **Sistema experto con reglas**: Similar a árbol pero con pesos. Mejor que el actual, pero las reglas se contradicen entre sí en el borde.
- **FSM con estados discretos**: Lo que tiene `decision.py`. No captura transiciones graduales; cada cambio de estado es una discontinuidad.

**Razón**: El utility scoring permite transiciones suaves, combina múltiples fuentes de información en una sola métrica (score), y escala naturalmente a nuevas razas/estrategias simplemente agregando fórmulas de utilidad a los YAML.

### D2: Biases continuos [0.0–1.0] en lugar de estrategias discretas

**Decisión**: El `BiasCalculator` produce un vector de biases continuos (e.g., `{stargate_units: 0.72, robo_units: 0.35, gateway_units: 0.55}`) que se usan como pesos en las fórmulas de utilidad.

**Alternativas consideradas:**
- **Estrategia única elegida al inicio**: Rígido, vulnerable a scouting falso, no permite pivots suaves.
- **Multi-armed bandit entre estrategias**: Elige una estrategia, la ejecuta hasta el final o pivotea completamente. No captura mixes de composición.

**Razón**: Los biases continuos permiten mezclar composiciones. No hay "estoy en Stargate" o "estoy en Robo" — hay "tengo 72% de inclinación a aire y 35% a ground mecánico". El output es fluido: a veces construyo Phoenix, a veces Immortal, a veces ambos. El scouting no "dispara" un cambio, sino que "empuja" los biases gradualmente.

### D3: YAML como fuente de verdad de estrategias

**Decisión**: Las estrategias y sus parámetros se definen en archivos YAML en `src/data/strategies/`. El código (`loader.py`) los parsea y valida contra un JSON Schema.

**Alternativas consideradas:**
- **Estrategias como clases Python**: Flexibles pero difíciles de mantener, modificar requiere deploy de código, no amigables para no-programadores.
- **JSON/TOML**: JSON no admite comentarios, TOML es menos conocido en Python.

**Razón**: YAML permite comentarios, es legible, y separa la definición de la estrategia de su ejecución. Esto permite iterar rápido en parámetros sin tocar código, y hace trivial agregar nuevas estrategias y razas. El JSON Schema asegura que los YAML sean válidos antes de cargarse.

### D4: Separación BiasCalculator / PriorityEngine

**Decisión**: Dos componentes separados con responsabilidades distintas:
- `BiasCalculator`: consume features + scouting → produce vector de biases
- `PriorityEngine`: consume biases + estado actual → evalúa acciones → retorna la mejor

**Alternativas consideradas:**
- **Un solo componente monolítico**: Más simple pero difícil de testear y extender.
- **Tres componentes (BiasCalculator → StrategySelector → Executor)**: Over-engineering para el scope actual.

**Razón**: La separación permite testear cada componente independientemente. El BiasCalculator puede mejorarse (agregar decaimiento, inferencia, ML) sin tocar el PriorityEngine. El PriorityEngine puede optimizarse (caching de scores, parallel eval) sin tocar el BiasCalculator.

### D5: Scouting con decaimiento temporal en lugar de snapshot binario

**Decisión**: La información de scouting tiene un campo `last_seen` (game_time) y un `confidence` que decae exponencialmente con el tiempo. El `BiasCalculator` usa `confidence = base_confidence * exp(-decay_rate * (now - last_seen))`.

**Alternativas consideradas:**
- **Solo lo visible ahora**: Ignora lo que vimos hace 30s. Un enemigo que esconde unidades es invisible.
- **Todo lo visto alguna vez**: Asume que el enemigo nunca cambia de composición. Falso.
- **Tracker de composición con timestamp fijo**: Similar pero menos expresivo que el decaimiento.

**Razón**: El decaimiento exponencial es matemáticamente simple y captura la intuición: si vi Mutaliscos hace 10s, probablemente sigan ahí. Si los vi hace 5 minutos, probablemente ya cambió.

### D6: FSM actual se preserva como capa de seguridad

**Decisión**: El FSM de `decision.py` no se elimina. Se refactoriza para que sus estados (DEFEND/ATTACK/RECOVER/SURRENDER/WON) actúen como "override" de alto nivel: si el FSM fuerza ATTACK (supply 200, desesperación), el PriorityEngine restringe sus acciones a solo unidades de ataque. Si fuerza SURRENDER, se detiene todo.

**Razón**: El utility engine puede producir outputs subóptimos en early game o situaciones extremas. El FSM actúa como safety net mientras el engine madura. Gradualmente, los overrides del FSM se irán reduciendo.

## Architecture

```
on_step(iteration)
  │
  ├─ extract_features()          → features dict (existente)
  ├─ detect_events()             → eventos (existente)
  │
  ├─ [NUEVO] BiasCalculator.update(features, events)
  │   ├─ Lee initial_biases del perfil YAML activo
  │   ├─ Aplica scouting_adjustments según features.enemy_army_composition
  │   ├─ Aplica decay temporal a observaciones viejas
  │   ├─ Aplica bias_speed para suavizar cambios
  │   └─ Produce: bias_vector (dict[str, float])
  │
  ├─ [NUEVO] PriorityEngine.evaluate(bias_vector, features)
  │   ├─ Para cada acción en todas las categorías:
  │   │   ├─ ¿Es alcanzable? (prerequisitos, recursos, supply)
  │   │   ├─ Evaluar fórmula de prioridad del YAML con biases actuales
  │   │   └─ Aplicar urgency modifiers (supply block, enemy at base)
  │   ├─ Seleccionar acción con mayor score
  │   └─ Retorna: Action(type, target, params)
  │
  ├─ [MODIFICADO] manage_*(context=action)
  │   ├─ Si action.type coincide con la categoría de este manage_*
  │   │   └─ Ejecutar action.target según action.params
  │   └─ Si no, skip (otro manage_* lo ejecutará)
  │
  └─ [EXISTENTE] logging, reportes, replay
```

### Data Flow

```
YAML profile ──load──► BiasCalculator.initial_biases
                          │
Scout/Observation ────────┤
  ├─ enemy_army_composition
  ├─ building_inference (nuevo)
  ├─ eco_inference (nuevo)
  └─ scout_age (nuevo)
                          │
Internal Metrics ─────────┤
  ├─ army_value_ratio
  ├─ supply_used
  ├─ bases, workers
  └─ tech_tree_state
                          │
                          ▼
                    bias_vector = {
                      stargate_units: 0.72,
                      robo_units: 0.35,
                      gateway_units: 0.55,
                      fast_expand: 0.40,
                      gas_heavy: 0.68,
                      air_upgrades: 0.70,
                      ground_upgrades: 0.30
                    }
                          │
                          ▼
                    PriorityEngine.evaluate(bias_vector, game_state)
                          │
                          ▼
                    Action(type=BUILD_UNIT, target=VOIDRAY, score=0.87)
                          │
                          ▼
                    manage_army() → train VOIDRAY con placement
```

### Perfil YAML (estructura)

```yaml
# data/strategies/protoss/standard_macro.yaml
name: standard_macro
race: Protoss
description: "Macro estándar con inclinación a gateway y transición a robo"

initial_biases:
  gateway_units: 0.6
  stargate_units: 0.2
  robo_units: 0.4
  fast_expand: 0.6
  gas_heavy: 0.4
  air_upgrades: 0.3
  ground_upgrades: 0.7

scouting_adjustments:
  enemy_air_heavy:          # cuando air_count enemigo > threshold
    condition: "enemy_army_analysis.air_count > 5"
    biases:
      stargate_units: +0.25
      air_upgrades: +0.20
      gateway_units: +0.10
  enemy_mech_heavy:
    condition: "enemy_army_analysis.mechanical_count > enemy_army_analysis.biological_count"
    biases:
      robo_units: +0.30
      gateway_units: +0.10
  enemy_bio_heavy:
    condition: "enemy_army_analysis.biological_count > 3"
    biases:
      robo_units: +0.15
      gateway_units: +0.20

priority_formulas:
  # Unidades
  STALKER: "(gateway_units * 0.6 + (1 - robo_units) * 0.3) * (1 - own_ratio('STALKER', 'army'))"
  ZEALOT: "gateway_units * 0.5 * (1 - own_ratio('ZEALOT', 'army'))"
  SENTRY: "gateway_units * 0.2 * (1 - own_ratio('SENTRY', 'army'))"
  IMMORTAL: "robo_units * 0.8 * (1 - own_ratio('IMMORTAL', 'army'))"
  COLOSSUS: "robo_units * 0.6 * ground_upgrades * (1 - own_ratio('COLOSSUS', 'army'))"
  VOIDRAY: "stargate_units * 0.7 * (1 - own_ratio('VOIDRAY', 'army'))"
  PHOENIX: "stargate_units * 0.5 * (1 - own_ratio('PHOENIX', 'army'))"

  # Edificios
  GATEWAY: "(gateway_units + (1 - robo_units) * 0.3) * max(0, (target_gateways - current_gateways) / target_gateways)"
  CYBERNETICSCORE: "gateway_units * (1 - has_cybercore)"
  STARGATE: "stargate_units * max(0, (target_stargates - current_stargates) / max(target_stargates, 1))"
  ROBOTICSFACILITY: "robo_units * max(0, (target_robos - current_robos) / max(target_robos, 1))"
  NEXUS: "fast_expand * 0.6 + (minerals > 500 ? 0.4 : 0)"
  FORGE: "ground_upgrades * (has_forge ? 0 : 1) * (minerals > 300 ? 0.5 : 0.2)"
  TWILIGHTCOUNCIL: "(gateway_units * 0.3) * (has_twilight ? 0 : 1) * (minerals > 300 and vespene > 100 ? 0.8 : 0.1)"

  # Upgrades
  WARPGATERESEARCH: "gateway_units * (has_warpgate ? 0 : 1)"
  PROTOSSGROUNDWEAPONSLEVEL1: "ground_upgrades * (has_weapons1 ? 0 : 1) * (has_forge ? 1 : 0)"

  # Eco
  PROBE: "1.0 * (workers < max_workers ? (1 - workers/max_workers) : 0)"
  PYLON: "supply_left < 4 ? 2.0 : 0.1"
  ASSIMILATOR: "gas_heavy * (assimilators < target_gas ? 1 : 0)"

meta:
  bias_speed: 0.3
  scout_decay_rate: 0.05
  max_workers: 70
  target_bases: 4
```

## Risks / Trade-offs

- **[Riesgo] El utility engine produce acciones subóptimas al inicio (cold start)** → Mitigación: el FSM actual se preserva como safety net; los perfiles YAML iniciales se calibran contra el comportamiento actual del bot para que el cambio sea conservador.
- **[Riesgo] Las fórmulas de utilidad requieren tuning manual** → Mitigación: es un feature, no un bug. El tuning manual es necesario para la fase inicial. ML futuro automatizará el tuning de parámetros usando datos de partidas.
- **[Riesgo] Evaluar N acciones cada step puede ser costoso** → Mitigación: cache de scores entre steps para acciones cuyo estado no cambió; evaluación lazy (solo acciones alcanzables); N típico es ~30-40 acciones, insignificante vs el resto del game loop.
- **[Riesgo] YAML malformado rompe el bot en runtime** → Mitigación: JSON Schema validation al cargar; tests que validan todos los YAML del directorio; fallback a perfil "safe_default" si la carga falla.
- **[Riesgo] Los biases pueden oscilar si bias_speed es muy alto** → Mitigación: bias_speed se configura por perfil; defaults conservadores (0.3); el sistema aplica exponential moving average para suavizar cambios bruscos de scouting.
- **[Riesgo] Regresión de comportamiento al refactorizar manage_*** → Mitigación: se escribe un test harness que compara decisiones del bot actual vs nuevo engine en partidas grabadas (features.jsonl existentes); el engine debe poder replicar el comportamiento actual con el perfil YAML correcto.

## Migration Plan

1. **Fase 1: Infraestructura** — Crear `src/strategies/` con loader, schemas, y perfiles YAML vacíos. Sin integrar al bot.
2. **Fase 2: BiasCalculator standalone** — Implementar `BiasCalculator` con tests unitarios. No se conecta al bot todavía.
3. **Fase 3: PriorityEngine standalone** — Implementar `PriorityEngine` con tests unitarios. Se valida contra partidas históricas (features.jsonl → qué hubiera decidido el engine).
4. **Fase 4: Integración** — Modificar `core.py` para conectar el engine. Los `manage_*` se refactorizan uno por uno (empezando por `manage_tech` y `manage_upgrades`).
5. **Fase 5: Calibración** — Crear el perfil YAML `standard_macro` que replique el comportamiento actual del bot. Validación con tests de regresión.
6. **Fase 6: Estrategias adicionales** — Agregar perfiles `stargate_open`, `robo_open`, `fast_expand` como variaciones del base.
7. **Rollback**: Cada fase es independiente. El FSM actual coexiste con el engine hasta la fase 4. Si el engine produce malas decisiones, el FSM puede override.

## Open Questions

- ¿Cuántos perfiles YAML iniciales necesitamos para Protoss? (mínimo 1: `standard_macro` que replique el comportamiento actual)
- ¿Las priority_formulas usan un DSL propio o expresiones Python evaluadas con `eval()` restringido? (recomendación: DSL simple con operadores básicos y funciones predefinidas, para seguridad)
- ¿El `bias_speed` debe ser global o por-biass? (recomendación: global con overrides opcionales por biass para fine-tuning futuro)
