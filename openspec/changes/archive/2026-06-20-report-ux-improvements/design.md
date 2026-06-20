## Context

Actualmente `generate_report_html()` produce un HTML con este orden: army columns, base saturation, supply sparkline, events table, metrics. La tabla de eventos vuelca cada evento individual (25,000+ filas para una partida típica) porque los detectores emiten por step sin consolidación. Las métricas están al final. No hay tracking de recursos recolectados — solo `minerals` y `vespene` actuales (unspent).

El reporte se abre vía `file://` desde el filesystem local. No requiere servidor web.

## Goals / Non-Goals

**Goals:**
- Dashboard de métricas al inicio con economía (recolectado, avg unspent, eficiencia) y ejército (max supply, army value peaks, T3)
- Eventos consolidados en rangos: agrupar eventos consecutivos del mismo tipo en (type, count, first, last, duration)
- Timeline d3.js interactivo (zoom/pan, tooltips, barras por tipo de evento) incrustado inline para compatibilidad `file://`
- `collected_minerals` y `collected_vespene` en el feature vector vía `bot.state.score`
- Army value enemigo con etiqueta `(visible)`

**Non-Goals:**
- No cambiar la estructura de report.json ni report.md
- No modificar la lógica de detección de eventos (events.py)
- No agregar gráficos de series temporales (supply/time, minerals/time) — eso es trabajo futuro
- No d3.js para comparación entre partidas (solo intra-partida)
- No CDN — todo debe funcionar offline con `file://`

## Decisions

### d3.js: embedding inline

**Decisión:** Leer `src/ml/vendor/d3.v7.min.js` desde disco al generar el HTML e incrustarlo como `<script>...</script>` inline.

**Alternativas consideradas:**
- CDN link: incompatible con `file://`, requiere internet
- Canvas puro: más laborioso, sin interactividad nativa
- CSS puro (barras con divs): sin zoom/pan, menos profesional

**Rationale:** El patrón ya existe en el proyecto — `render_unit_icon_svg()` inlinea SVG. d3.js v7 minificado pesa ~250KB, aceptable para un reporte offline. Por partida, con 11 reportes actuales, el overhead total es ~2.7MB en disco.

### Event consolidation algorithm

**Decisión:** Colapsar eventos consecutivos del mismo tipo en rangos. Un "rango" se define como una secuencia ininterrumpida de eventos con el mismo `type`. La consolidación ocurre en `_build_event_ranges()` — nueva función en `report.py`.

```
Input:  [supply_block@120s, supply_block@120.18s, ..., supply_block@2300s,
         resource_float@300s, resource_float@300.18s, ...]
Output: [
  {type: "supply_block", count: 8180, first: 120.0, last: 2300.0, severity: "high", duration: 2180.0},
  {type: "resource_float", count: 8398, first: 300.0, last: 900.0, severity: "medium", duration: 600.0},
  ...
]
```

**Edge case:** Eventos puntuales (tech_milestone, expansion_started, game_start, enemy_push) típicamente tienen count=1 y duration=0. Se muestran como marcadores en el timeline, no como barras.

**Rationale:** Reduce 25,000+ filas a ~10-15. La información relevante (cuándo empezó/terminó una condición) se preserva. Los detalles paso a paso siguen disponibles en `events.jsonl` para análisis posteriores.

### d3 timeline data structure

**Decisión:** Dos colecciones en el JSON del timeline:
- `ranges[]`: eventos persistentes con `{type, severity, ranges: [{start, end, count}]}` — barras horizontales
- `points[]`: eventos puntuales con `{type, time, severity, details}` — marcadores

El timeline se renderiza como SVG con:
- Eje Y: lanes por tipo de evento (orden: severidad alta primero, luego media, luego info)
- Eje X: tiempo de juego (0 a duración)
- Barras: `<rect>` con fill por severidad (high=#e94560, medium=#f5c542, info=#4a9eff)
- Puntos: `<circle>` o `<polygon>` (diamond) para eventos puntuales
- Zoom: `d3.zoom()` con scaleExtent [1, 50], translateExtent para evitar scroll infinito
- Tooltip: `<div>` overlay posicionado con `pointer` event

**Rationale:** La separación ranges/points permite renderizado distinto para cada tipo. El diseño de lanes tipo "swimlane" es estándar en herramientas de observabilidad y familiar para developers.

### Resource tracking via bot.state.score

**Decisión:** Agregar `collected_minerals` y `collected_vespene` a `extract_features()` usando `bot.state.score.collected_minerals` y `bot.state.score.collected_vespene`. Se capturan en cada frame (valor acumulativo). La eficiencia se calcula en `_compute_metrics()` como:

```
efficiency = (collected - avg_unspent_per_step * total_steps) / collected
```

donde `collected` es el valor del último frame y `avg_unspent_per_step` es `(sum unspent) / total_steps`.

**Rationale:** python-sc2 expone estos valores a través de `self.state.score`. Son acumulativos — el último frame contiene el total de la partida. Capturarlos por frame permite análisis temporal futuro sin costo adicional.

### HTML layout reorder

**Decisión:** Nuevo orden de secciones en `generate_report_html()`:

1. Header (match info, resultado, duración)
2. Metrics Dashboard (economy | army, two-column)
3. Events Summary Table (consolidada)
4. d3 Timeline (interactive SVG)
5. Our Army / Enemy Army (two-column, existing)
6. Base Saturation (existing)
7. Supply sparkline (existing)

**Rationale:** Las métricas y el timeline son lo primero que un analista quiere ver. El detalle de composición de ejército y saturación por base es secundario.

## Risks / Trade-offs

- **d3.js 250KB por reporte** → Aceptable. Un reporte de partida típico con 13K features y 25K eventos ya pesa ~2MB en JSON. 250KB extra no es significativo.
- **`bot.state.score` podría ser None** → Mitigación: verificar `hasattr(bot, 'state') and bot.state and bot.state.score` antes de acceder. Si no está disponible, `collected_minerals = 0`.
- **Consolidación de eventos puede perder detalle** → Los eventos individuales siguen en `events.jsonl`. La consolidación es solo para presentación. La tabla muestra count para indicar frecuencia.
- **d3 timeline en partidas muy largas (1h+)** → El zoom de d3 maneja esto nativamente. Las barras se comprimen pero el usuario hace zoom para ver detalle.

## Open Questions

- ¿Descargar d3.v7.min.js manualmente o automatizar en `uv sync`? → Manual por ahora (un archivo, una vez). Se documenta en AGENTS.md.
