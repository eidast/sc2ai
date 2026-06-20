## Context

El bot extrae saturación por base como un ratio agregado (`ideal_workers = minerals*2 + gas*3`, `ratio = current/ideal`). Esto mezcla mineral y gas en un solo número, impide diagnosticar si el déficit es de mineral o gas, y no detecta workers ociosos. El motor estratégico (BiasCalculator, PriorityEngine) recibe features y builtins pero no tiene visibilidad de saturación por tipo de recurso. El auto-tuner (`tune_strategies.py`) analiza métricas agregadas pero sin dimensión temporal.

La modificación toca 7 archivos en 4 capas: observación, motor del bot, reportes, y auto-tuner.

## Goals / Non-Goals

**Goals:**
- Desglosar saturación por base en mineral vs gas, con detección de idle workers y clasificación de estado
- Transferir workers autónomamente de bases sobresaturadas a subsaturadas
- Usar workers ociosos/sobrantes para scouting secundario sin costo de mining
- Capturar timeline de saturación en el reporte para análisis post-partida
- Exponer métricas de saturación como builtins en el motor de fórmulas
- Alimentar el auto-tuner con datos temporales de saturación

**Non-Goals:**
- No se modifica el state machine de decisiones (DEFEND/ATTACK/RECOVER/SURRENDER)
- No se añaden nuevas dependencias externas
- No se modifica la estructura de `StrategyProfile` ni los tipos `Action`/`ActionType`
- No se implementa un modelo ML — solo se preparan los datos
- No se modifican los perfiles YAML de estrategia salvo las fórmulas de PROBE, NEXUS, y ASSIMILATOR

## Decisions

### 1. Conteo de workers por tipo de recurso

**Opción A — Estimación**: `mineral_workers ≈ total - gas_buildings*3`, asumiendo gas siempre lleno. Simple pero impreciso si el gas no está saturado.

**Opción B — Conteo real**: Iterar `bot.workers`, para cada worker ver qué recolecta (`worker.orders`), asignarlo a la base más cercana por posición.

**Decisión: Opción B.** El costo es ~50-70 workers por step, negligible. La precisión vale la pena especialmente para detectar idle workers y workers en tránsito. Los workers que no están recolectando (idle, atacando, construyendo) se clasifican como idle para su base más cercana.

### 2. Estructura del campo `bases` en features

Se expande de 6 campos a 14 campos por base:

```python
{
    "position": (x, y),
    # --- Campos existentes (retenidos) ---
    "ideal_workers": int,       # ideal total (mineral*2 + gas*3)
    "current_workers": int,     # nexus.assigned_harvesters
    "saturation_ratio": float,  # current / ideal (renombrado a total_saturation)
    "army_nearby": int,
    "enemy_nearby": int,
    # --- Nuevos campos ---
    "mineral_patches": int,
    "gas_geysers": int,
    "ideal_mineral_workers": int,
    "ideal_gas_workers": int,
    "actual_mineral_workers": int,
    "actual_gas_workers": int,
    "idle_workers_nearby": int,
    "mineral_saturation": float,
    "gas_saturation": float,
    "total_saturation": float,   # antes saturation_ratio
    "status": str,               # "undersaturated" | "optimal" | "oversaturated"
}
```

**Thresholds de status:**
| Condición | Status |
|---|---|
| `mineral_saturation > 1.1` (17+ en 8 patches) | `oversaturated` |
| `gas_saturation > 1.0` (4+ por geyser) | `oversaturated` |
| `mineral_saturation < 0.7` o `gas_saturation < 0.5` con geysers | `undersaturated` |
| resto | `optimal` |

**Retrocompatibilidad**: `saturation_ratio` se renombra a `total_saturation`. El código existente que lee `saturation_ratio` se actualiza. Los tests existentes que acceden a campos de `bases` se adaptan.

### 3. Worker Transfer — Algoritmo autónomo

**Alternativa considerada**: Hacer que el PriorityEngine emita `Action(type=WORKER_TRANSFER)` y que `manage_probes` lo ejecute. Descartado: complica el sistema de acciones sin beneficio real — transferir workers no es una decisión estratégica sino optimización operativa.

**Decisión**: Autónomo, dentro de `manage_probes()`, análogo a `_assign_gas_workers()`. Una acción por step, con prioridades:

```
manage_worker_transfer():
  1. PRIORIDAD: Gas desatendido
     Si hay geyser con <3 workers → tomar idle o mineral worker de base más saturada
     → worker.gather(assimilator)

  2. PRIORIDAD: Base oversaturada → undersaturada
     Si oversaturated_bases > 0 Y undersaturated_bases > 0:
       donor = idle o mineral_worker #17+ de oversat
       → worker.gather(mineral_field cerca de target)

  3. PRIORIDAD: Late game recycling
     Si game_time > 900 Y mineral_saturation > 1.3 en TODAS las bases:
       → no entrenar más probes (MAX_WORKERS dinámico = bases * 16)
```

**MAX_WORKERS dinámico**: En late game, el cap de workers baja porque los patches se agotan. `ideal_workers` baja naturalmente al desaparecer patches, y `total_saturation` sube automáticamente disparando los thresholds de transfer. Adicionalmente, se calcula `dynamic_max = sum(b.ideal_workers for b in bases) * 1.1`, y `MAX_WORKERS = min(70, dynamic_max)`.

### 4. Worker Scout — Integración en manage_scout

**Alternativa considerada**: Sistema de scouting separado con su propio state machine. Descartado: duplica infraestructura.

**Decisión**: Segundo hilo dentro de `manage_scout()`, reutilizando waypoints compartidos. Diferencias con el scout principal:

| Aspecto | Scout principal | Worker scout |
|---|---|---|
| Unidad | Probe designada | Worker idle de base oversat |
| Retreat | Sí, <50% HP | No, es desechable |
| Propósito | Descubrir bases, monitorear army | Ver expansiones no visitadas |
| Activación | Siempre (early game) | Solo con idle > 1 o mineral_sat > 1.2 |
| Fin de vida | Si muere → DEAD, se reemplaza | Si muere → fin. Si completa loop → vuelve a minar |

Estado persistente mínimo: `_worker_scout_tag`, `_worker_scout_waypoint_index`, `_worker_scout_active`.

### 5. Saturation Timeline

Snapshots capturados cada 60s (mismo intervalo que `_build_army_snapshots`). Se añade `_build_saturation_snapshots()` en `report.py`.

Estructura:
```python
"saturation_timeline": [
    {
        "time": 60,
        "bases": [{
            "base": 0,
            "mineral_workers": int, "gas_workers": int,
            "mineral_saturation": float, "gas_saturation": float,
            "status": str, "idle": int,
        }],
        "totals": {
            "workers": int, "bases": int,
            "oversaturated_bases": int, "undersaturated_bases": int,
            "idle_workers": int,
            "avg_mineral_sat": float, "avg_gas_sat": float,
        }
    },
    ...
]
```

Esta estructura es autocontenida (no requiere el `features.jsonl` completo) para que el auto-tuner y futuros pipelines ML puedan consumirla directamente desde `report.json`.

### 6. Builtins para el motor de fórmulas

Se añaden a `prepare_builtins()`:

```python
"undersaturated_bases": sum(1 for b in features["bases"] if b["status"] == "undersaturated"),
"oversaturated_bases": sum(1 for b in features["bases"] if b["status"] == "oversaturated"),
"idle_workers": sum(b["idle_workers_nearby"] for b in features["bases"]),
"avg_mineral_sat": promedio de mineral_saturation,
"avg_gas_sat": promedio de gas_saturation,
```

Las fórmulas YAML existentes que usan `workers` y `bases` se mantienen funcionales. Solo se modifican PROBE, NEXUS, y ASSIMILATOR para usar los nuevos builtins:

```yaml
PROBE: (workers < 70 and undersaturated_bases > 0 ? (1 - workers / 70) : 0)
NEXUS: fast_expand * 0.6 + (oversaturated_bases > 0 and minerals > 300 ? 0.5 : 0) + (minerals > 500 ? 0.2 : 0)
ASSIMILATOR: gas_heavy * (has_structure('ASSIMILATOR') < bases * 2 ? 1 : 0) * (avg_mineral_sat > 0.8 ? 1 : 0.5)
```

### 7. Auto-Tuner con datos temporales

`tune_strategies.py` actualmente analiza métricas agregadas por partida. Con `saturation_timeline` se añaden:

| Métrica nueva | Qué ajusta |
|---|---|
| `avg_oversat_duration` (tiempo con bases sobresaturadas) | `fast_expand`, `max_workers` |
| `t_first_gas_saturated` (cuándo se llena el primer gas) | `gas_heavy` |
| `t_expand_2` (tiempo de la segunda expansión) | `fast_expand` |
| `idle_worker_minutes` (minutos acumulados con workers ociosos) | `fast_expand` (subir), `gateway_units` (bajar) |
| `saturation_stability` (varianza entre bases) | mantener/incrementar `bias_speed` |

El tuner compara wins vs losses en estas métricas y ajusta biases en la dirección que favorece wins. Se preserva el comportamiento de backup (.yaml.bak) existente.

## Risks / Trade-offs

- **[Riesgo] Worker transfer en mapas grandes**: Mover un worker entre bases lejanas cuesta ~15-25s de viaje sin minar. Break-even: ~20s si el nuevo destino tiene 100% eficiencia vs 50% en origen. → **Mitigación**: Solo transferir cuando el destino está significativamente subsaturado (mineral_saturation < 0.7) y limitar a 1-2 workers por step.
- **[Riesgo] Worker scout muere sin obtener info**: Si el worker scout entra a una base defendida, muere instantáneamente. → **Mitigación**: Solo se usa en mid/late game, y los workers son excedentes — su pérdida no afecta la economía.
- **[Riesgo] Timeline aumenta tamaño de report.json**: Con partidas de 30+ minutos, son ~30 snapshots con datos de múltiples bases. → **Mitigación**: Cada snapshot es < 1KB. Para 3 bases × 30 snapshots ≈ 30KB adicionales en el JSON, insignificante.
- **[Trade-off] Conteo real de workers vs estimación**: Iterar `bot.workers` cada step añade ~50-70 iteraciones. Impacto despreciable (~0.1ms) pero si se detecta overhead se puede muestrear cada N steps para el conteo real y estimar en steps intermedios.
