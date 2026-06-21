## Context

El proyecto tiene 4 perfiles de estrategia YAML, shadow profiles funcionando, y `decisions.jsonl` con predicciones multi-perfil. Faltan herramientas de análisis y el motor de prioridad tiene bugs/limitaciones: recomienda unidades sin verificar tech tree, y no tiene inercia entre acciones consecutivas.

## Goals / Non-Goals

**Goals:**
- Script `analyze_shadows.py` que lea JSONL y produzca métricas (agreement, distribución, sesgos, timeline)
- `PriorityEngine._is_reachable()` verifique `requires` del YAML antes de recomendar
- `PriorityEngine.evaluate()` aplique bonus de momentum (+15%) por continuidad
- Perfiles YAML extienden su schema con `requires` y `max_count` opcionales

**Non-Goals:**
- Dashboard interactivo (HTML/JS)
- ML/AI para tuning de fórmulas
- Cambiar el comportamiento de los `manage_*()` existentes
- Agregar dependencias externas (solo stdlib)

## Decisions

### 1. Script de análisis: formato de salida

**Decisión**: Salida en texto plano estructurado (tablas ASCII + timeline). Opcional `--format json` para consumo programático.

**Alternativas**: HTML, CSV, matplotlib. Rechazadas por agregar dependencias. El texto es inmediato en terminal y JSON se puede pipear a otras herramientas.

### 2. Tech tree: schema YAML

**Decisión**: Campo `requires` opcional en cada entrada de `priority_formulas`:

```yaml
priority_formulas:
  COLOSSUS:
    formula: "robo_units * 0.6 * ..."
    requires: ["ROBOTICSBAY"]
```

El loader acepta tanto el formato antiguo (string simple) como el nuevo (dict con `formula` + `requires`). Esto es backward-compatible.

**Alternativa**: Hardcodear el tech tree en Python. Rechazado porque cada perfil puede tener diferentes prerequisitos (ej. un perfil hipotético "carrier_rush" podría requerir FLEETBEACON para CARRIER pero otro no).

### 3. Momentum: implementación

**Decisión**: Bonus multiplicativo fijo de +15% cuando `prev_action.target == candidate.target AND prev_action.type == candidate.type`. Se aplica después de `evaluate_formula()`, antes del argmax.

**Alternativa**: Sistema de "commitment" con decay exponencial. Rechazado por complejidad innecesaria — el objetivo es evitar saltos erráticos, no simular psicología.

**Valor 1.15**: Suficiente para inclinar decisiones cercanas (0.80 → 0.92) sin sobrepasar diferencias grandes (0.50 → 0.58, no alcanza a 0.90). Si dos candidatos son muy cercanos, gana el que ya veníamos haciendo.

### 4. Prioridad entre mejoras

**Decisión**: El tech tree se ejecuta primero (filtra), el momentum después (ordena). Si un candidato es filtrado por tech tree, el momentum no lo considera. Esto es correcto: no tiene sentido preferir algo imposible.

### 5. Análisis: métricas incluidas

**Decisión**: 4 bloques de métricas:
1. **Overview**: total steps, game time, result, strategic state distribution, override rate
2. **Agreement matrix**: matriz N×N de % de coincidencia entre perfiles (target igual)
3. **Action distribution**: top-3 acciones por perfil con score promedio y desviación
4. **Bias evolution**: valor inicial → final de cada bias key + delta
5. **Timeline**: tabla de hitos (cambio de estado, primera divergencia, etc.)

## Risks / Trade-offs

- **[Tech tree] Requiere actualizar YAMLs**: Todos los perfiles necesitan `requires` en fórmulas relevantes. → Mitigación: solo 4 perfiles, ~5-8 fórmulas con requires por perfil. Carga manual baja.
- **[Momentum] Puede causar "stuck" en una acción**: Si STALKER siempre gana por momentum, nunca se construye otra unidad. → Mitigación: el bonus es solo +15%, no bloquea cambios. Las fórmulas de saturación (`own_ratio`) naturalmente reducen el score cuando ya hay muchas unidades de ese tipo.
- **[Script] Depende de que el match tenga datos**: Si `decisions.jsonl` no existe o está vacío, el script falla con mensaje claro. → Mitigación: validación temprana de archivos.
