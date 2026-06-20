## Why

La saturación de bases actual es un solo número (`ideal_workers` y `ratio`) que mezcla mineral y gas, ocultando si el déficit está en minerales (ingreso base) o en gas (tech). El reporte solo muestra una instantánea del último frame. Además, el bot nunca mueve workers entre bases — si una base se sobresatura y otra está vacía, los workers sobrantes se quedan ahí sin aportar, y en late game ese supply podría ser army. El auto-tuner actual no tiene visibilidad temporal de la economía.

## What Changes

- **Observation enriquecida**: `_extract_base_features` desglosa mineral vs gas por base, detecta idle workers, y clasifica estado (undersaturated / optimal / oversaturated). El campo `bases` en features se expande.
- **Worker transfer autónomo**: Nuevo `manage_worker_transfer()` en `core.py` — mueve workers de bases sobresaturadas a subsaturadas, reasigna mineral→gas cuando hay déficit de gas, y en late game frena la producción de probes para liberar supply.
- **Worker scout**: `manage_scout()` gana un hilo secundario que usa workers ociosos o sobrantes para espiar expansiones enemigas no visitadas, sin sacrificar mining real.
- **Saturation timeline**: El reporte captura snapshots de saturación cada 60s (`saturation_timeline`), visibles en el HTML y usables por el auto-tuner.
- **Dashboard enriquecido**: El HTML muestra cards por base con barras mineral/gas y estado.
- **Builtins para el motor**: `prepare_builtins` expone `undersaturated_bases`, `oversaturated_bases`, `idle_workers`, `avg_mineral_saturation`, `avg_gas_saturation` para uso en fórmulas YAML.
- **Fórmulas YAML actualizadas**: PROBE y NEXUS usan los nuevos builtins para decidir con conciencia de saturación real.
- **Auto-tuner con datos temporales**: `tune_strategies.py` analiza `saturation_timeline` para ajustar `fast_expand`, `gas_heavy`, `max_workers`, y detectar problemas de timing en la economía.

## Capabilities

### New Capabilities
- `worker-transfer`: redistribución autónoma de workers entre bases, reasignación mineral→gas, y reciclaje en late game.
- `saturation-timeline`: captura de snapshots temporales de saturación por base para reportes, auto-tuning, y datos de entrenamiento ML.

### Modified Capabilities
- `per-base-saturation`: los datos de saturación por base se desglosan en mineral vs gas, incluyen idle workers, y clasifican estado.
- `observation-pipeline`: el contrato del campo `bases` en features se expande con nuevos campos requeridos.
- `report-metrics-dashboard`: se añaden cards de saturación por base con breakdown mineral/gas.
- `report-event-timeline`: se añade `saturation_timeline` al JSON del reporte y se visualiza en el timeline d3.
- `scout-behavior`: se añade hilo secundario de scouting con workers ociosos/sobrantes.
- `bot-gameplay`: se añade `manage_worker_transfer()` a la secuencia de managers en `on_step()`.

## Impact

- `src/ml/observation.py` — `_extract_base_features()` se expande
- `src/ml/report.py` — `_compute_metrics()`, `generate_report_html()`, `generate_report_md()`
- `src/bot/core.py` — nuevo `manage_worker_transfer()`, `_get_rich_saturation()`, extender `manage_scout()`
- `src/strategies/formula.py` — `prepare_builtins()` con nuevos agregados
- `src/data/strategies/protoss/*.yaml` — fórmulas de PROBE, NEXUS, ASSIMILATOR
- `scripts/tune_strategies.py` — nuevas métricas desde `saturation_timeline`
- `tests/` — tests para observation enriquecida, worker transfer, worker scout, saturation timeline
