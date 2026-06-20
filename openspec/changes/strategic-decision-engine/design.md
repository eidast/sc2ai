## Context

El bot actualmente ejecuta un `manage_attack()` con threshold fijo de 200 supply y un booleano `attack_triggered`. El análisis de 4 partidas revela que nunca alcanza ese umbral (max 112-141). El enemigo (Terran Medium) escala a T3 consistentemente mientras nosotros producimos Stalkers/Zealots. La muerte es inevitable y predecible.

La infraestructura de features (`observation.py`) ya captura composición de ejército, HP, DPS, y tiene una base de datos de unidades con costos. Lo que falta es un motor que use esos datos para tomar decisiones.

## Goals / Non-Goals

**Goals:**
- Reemplazar `attack_triggered` booleano por un FSM con estados DEFEND, ATTACK, RECOVER, SURRENDER
- Implementar thresholds de ataque adaptativos por fase temporal, raza enemiga y fog-of-war
- Añadir métricas de army_value (costo económico) a los features de observación
- Detectar unidades T3 enemigas para evaluar ventanas de ataque/surrender
- Implementar surrender condicional (configurable, apagado por defecto)
- Crear script de análisis batch de partidas pasadas

**Non-Goals:**
- Micro-management (focus fire, kiting, splitting) — queda para otro change
- Modificar `manage_scout()` — se consumen sus datos pero no se modifica
- Modificar `manage_defense()` — sigue igual, solo interactúa con el estado del FSM
- Nuevos tipos de unidad o producción (Robotics, Stargate)
- ML model integration — heuristic engine primero, ML después
- Cambiar build order — sigue siendo gateways → cyber → expand

## Decisions

### 1. FSM con 4 estados sobre reglas binarias

**Chosen**: Máquina de estados finita con DEFEND → ATTACK → RECOVER → SURRENDER
**Alternatives**: Sistema de reglas if/elif anidadas, o scoring ponderado

Rationale: Una FSM es testeable, debuggeable, y previene oscilaciones (hysteresis). Cada transición tiene condiciones claras. Las reglas anidadas llevan a behavior impredecible con múltiples señales. El scoring ponderado requiere calibración de pesos que no tenemos datos para hacer.

```
DEFEND ──(ventaja)──▶ ATTACK
  ▲                    │
  │               (army muerto)
  │                    ▼
  │                RECOVER ──(sin comeback)──▶ SURRENDER
  └──(eco + army ok)──┘
```

### 2. Army value como métrica principal sobre HP/DPS

**Chosen**: `Σ count × (mineral_cost + vespene_cost)` excluyendo workers
**Alternatives**: HP total, DPS combinado, supply count

Rationale: El valor económico refleja mejor la inversión real. HP infla a unidades tanque (Thor: 400 HP = 500 cost) vs unidades frágiles (Marine: 45 HP = 50 cost). 10 Marines (450 HP, 500 cost) son menos peligrosos que 1 Thor (400 HP, 500 cost) pero el HP crudo los hace parecer equivalentes. Army value corrige esto. Supply count es demasiado burdo (un Battlecruiser = 3 Marines en supply pero no en poder).

### 3. T3 detection: mapeo estático por raza

**Chosen**: Dict `T3_UNITS` en `strategy.py` con nombres de unidades por raza
**Alternatives**: Inferir del costo (costo > X), del supply (supply > Y), o del tech tree

Rationale: Un mapeo explícito es preciso y mantenible. Inferir del costo falla con unidades caras T2 (Immortal: 350 cost pero es T2.5, no T3). El tech tree requiere modelar dependencias de edificios, complejidad innecesaria ahora.

### 4. Thresholds adaptativos: tabla por fase + multiplicadores

**Chosen**: Tabla de thresholds por fase temporal con multiplicadores por raza y fog
**Alternatives**: Fórmula única continua, o thresholds fijos idénticos para todo

Rationale: Las fases del juego tienen dinámicas distintas. Un push a los 4 min con 30 supply puede ser letal; a los 15 min es suicida. La raza enemiga afecta la velocidad de producción (Zerg > Terran > Protoss). El fog añade incertidumbre que requiere umbrales más conservadores.

| Fase | Tiempo (s) | Supply min | Condición |
|------|-----------|-----------|-----------|
| Early | < 240 | 30 | army_value_ratio > 1.5 |
| Mid | 240-600 | 80 | army_value_ratio > 1.2 |
| Late | 600-900 | 100 | ó enemy_T3 > 0 |
| Desperate | > 900 | 60 | siempre (o surrender) |

Multiplicadores: vs Zerg ×0.85, vs Terran ×1.0, vs Protoss ×1.1, fog ×1.3.

### 5. Surrender: multi-condición con histéresis temporal

**Chosen**: `game_time > 300 AND army_value_ratio < 0.15 AND eco_ratio < 0.3 AND sustained 120s AND NOT attacking`
**Alternatives**: Surrender inmediato al cruzar threshold, o solo por eco

Rationale: SC2 permite comebacks. Un déficit momentáneo no debe activar surrender. 120s (4 min juego en fastest) es suficiente para confirmar que no hay recuperación. La condición `NOT attacking` evita rendirse en medio de un push. La eco muerta (workers < 10 o bases == 0) es señal definitiva.

### 6. Script de análisis: lectura de reports existentes

**Chosen**: `scripts/analyze.py` que lee `reports/*/report.json` y `features.jsonl`
**Alternatives**: Análisis en tiempo real durante el juego, o herramienta externa

Rationale: Los datos ya existen en disco. Un script Python simple puede leerlos sin modificar nada. Sirve para calibrar thresholds después de varias partidas y detectar patrones. Es la base para un futuro "auto-tuning" de parámetros.

### 7. CLI flags: opt-in para surrender y fog

**Chosen**: `--surrender` y `--fog` como flags opcionales (off por defecto)
**Alternatives**: `--no-surrender` (on por defecto), o thresholds en config file

Rationale: El comportamiento actual (no surrender, no fog) es el default. Los flags son opt-in para no romper nada. Un config file sería overkill para 2 flags ahora; se puede migrar después.

## Risks / Trade-offs

- **[Risk] Thresholds mal calibrados causan ataques suicidas** → Mitigation: El script `analyze.py` permite recalibrar con datos reales. Los thresholds empiezan conservadores (army_value_ratio > 1.5 en early).
- **[Risk] Surrender prematuro en partidas remontables** → Mitigation: 120s de sostenimiento + no surrender durante ataque + solo después de 5 min. El flag `--surrender` es opcional.
- **[Risk] army_value no captura valor de upgrades** → Acceptable: Los upgrades son un multiplicador, no una unidad. Se pueden añadir después como factor de ajuste al army_value.
- **[Trade-off] Sin micro, ataques contra T3 pueden ser ineficientes** → Acceptable: La regla actual es conservadora (si enemy_T3 > 0 y nosotros sin T3, no atacar a menos que sea desperate). El micro se implementará en otro change.
- **[Trade-off] T3_UNITS es estático y manual** → Acceptable: SC2 no recibe balance patches. Si cambia algo, se actualiza el dict.

## Migration Plan

No migration needed — todos los cambios son aditivos o reemplazan lógica existente sin cambiar interfaces externas.

1. `extract_features()` añade campos nuevos sin quitar los existentes → backward compatible
2. `MyBot.__init__()` acepta nuevos params con defaults que preservan comportamiento actual
3. `manage_attack()` usa el nuevo decision engine, pero sin `--surrender` ni thresholds nuevos, el comportamiento es idéntico (espera 200 supply)
4. El FSM reemplaza `attack_triggered` como atributo interno

Rollback: revertir el commit. No hay migración de datos ni cambios de formato.
