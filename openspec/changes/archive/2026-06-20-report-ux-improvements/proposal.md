## Why

El reporte HTML actual es difícil de leer y poco informativo. La sección de eventos vuelca 25,000+ filas (una por step), las métricas clave están al fondo de la página, y no hay forma de comparar economía real (minerales recolectados vs gastados). Necesitamos un reporte que permita entender una partida de un vistazo — métricas al principio, eventos consolidados en rangos, y un timeline interactivo con d3.js para explorar la línea temporal.

## What Changes

- **Dashboard de métricas al inicio**: Tarjeta de economía (minerales/vespene recolectados, avg unspent, eficiencia de gasto, peak workers) y ejército (max supply, army value peak, T3 counts). Reemplaza la sección de métricas actual que estaba al final.
- **Eventos consolidados**: Agrupar eventos consecutivos del mismo tipo en rangos con count, first, last y duration. De ~25,000 filas a ~10-15 filas. Tabla de resumen y datos para el timeline.
- **Timeline interactivo con d3.js**: Visualización estilo Chrome DevTools Network tab — barras horizontales por tipo de evento con zoom/pan, tooltips, y marcadores para eventos puntuales. d3.js v7 incrustado inline (sin CDN, compatible con `file://`).
- **Métricas de recolección total**: `collected_minerals` y `collected_vespene` capturados desde `bot.state.score` en el pipeline de observación. Cálculo de eficiencia `(recolectado - avg_unspent × steps) / recolectado`.
- **Army value enemigo**: Mostrado con etiqueta `(visible)` para indicar que es un lower bound bajo fog-of-war.

## Capabilities

### New Capabilities
- `report-metrics-dashboard`: Tarjeta consolidada de métricas al inicio del reporte HTML con economía, ejército y resumen de eventos
- `report-event-timeline`: Timeline interactivo d3.js con consolidación de eventos en rangos, zoom/pan, y tooltips
- `resource-collection-tracking`: Seguimiento de minerales y vespene recolectados totales vía `bot.state.score`

### Modified Capabilities
- `observation-pipeline`: `extract_features()` SHALL devolver `collected_minerals` y `collected_vespene` desde el score de juego, y `efficiency` calculado por el reporte

## Impact

- **Nuevos archivos**: `src/ml/vendor/d3.v7.min.js` (d3.js v7 minificado, ~250KB)
- **Modificados**: `src/ml/report.py` (nuevo layout HTML, consolidación de eventos, timeline d3, métricas dashboard), `src/ml/observation.py` (nuevos campos collected_minerals/vespene), `src/bot/core.py` (uso de score para collected resources)
- **Nuevos tests**: `tests/test_report_ux.py` (dashboard, event consolidation, timeline data)
- **Tests modificados**: `tests/test_observation.py` (nuevos campos en feature vector)
- **Nueva dependencia**: d3.js v7 (embebida en repo, no pip dependency)
- **No breaking changes**: El JSON y MD del reporte no cambian estructura. El HTML es puramente aditivo.
