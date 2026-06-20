## Why

El bot actualmente espera hasta 200 supply para atacar — un umbral que jamás alcanza (partidas analizadas: max supply 112-141). Muere defendiendo pasivamente mientras el enemigo escala a T3 (Battlecruisers, Thors, Siege Tanks) sin oposición. Las 4 partidas registradas son derrotas, con duraciones de 17-22 minutos desperdiciadas en un _death spiral_ predecible. Necesitamos un motor de decisión que evalúe cuándo atacar, cuándo defender, y cuándo rendirse para acelerar simulaciones.

## What Changes

- **Motor de decisión estratégica** (`src/bot/decision.py`): FSM con 4 estados — DEFEND, ATTACK, RECOVER, SURRENDER — que reemplaza la lógica binaria `attack_triggered=True/False` por una evaluación multi-señal en cada paso.
- **Ataque dinámico**: Umbrales de ataque adaptativos por fase temporal (early/mid/late/desperate), raza enemiga, presencia de fog-of-war, y confianza de scouting. Ya no se espera un supply fijo de 200.
- **Surrender inteligente**: El bot se rinde (`chat_send("gg")`) cuando el déficit de `army_value` es insalvable (< 0.15) sostenido por 120s, con la economía muerta, y fuera de early game (> 300s). Configurable con `--surrender` en el CLI.
- **Métrica `army_value`**: Cálculo de valor económico del ejército (Σ mineral_cost + vespene_cost) excluyendo workers, tanto propio como enemigo. Reemplaza el HP crudo como métrica principal de decisión.
- **Detección de T3 enemigo**: Identificación de unidades de alto nivel tecnológico enemigo (Battlecruiser, Thor, Broodlord, Carrier, etc.) para activar ventanas de ataque de último recurso o surrender.
- **Script de análisis batch** (`scripts/analyze.py`): Lee todas las partidas en `reports/` y genera insights comparativos: tendencias de army_value, puntos de quiebre, detección de T3, y recomendaciones de thresholds.

## Capabilities

### New Capabilities
- `strategic-decision`: Motor de decisión con FSM de 4 estados que evalúa ataque, defensa, recuperación y surrender basado en métricas del juego
- `army-value-metrics`: Cálculo de valor económico del ejército (mineral + gas) excluyendo trabajadores, con ratios y trending

### Modified Capabilities
- `bot-gameplay`: El umbral de ataque deja de ser un valor fijo (200 supply). `manage_attack()` ahora consume el estado del decision engine en lugar de un booleano. Se añade `manage_surrender()` al dispatch de `on_step()`. Los thresholds son adaptativos por fase temporal, raza enemiga, y fog-of-war.
- `observation-pipeline`: `extract_features()` devuelve nuevos campos: `our_army_value`, `enemy_army_value`, `enemy_t3_count`, `our_t3_count`, `enemy_worker_count`, `army_value_ratio`

## Impact

- **Nuevos archivos**: `src/bot/decision.py`, `scripts/analyze.py`
- **Modificados**: `src/bot/core.py` (dispatch, init params, attack/surrender logic), `src/bot/strategy.py` (constantes por fase/raza, T3 mapping), `src/ml/observation.py` (nuevos campos), `scripts/run.py` (flags `--surrender`, `--fog`)
- **Nuevos tests**: `tests/test_decision.py`
- **Tests modificados**: `tests/test_observation.py`
- **No new dependencies**: Todo usa python-sc2 API existente y stdlib
- **No breaking changes**: `ATTACK_SUPPLY=200` legacy se preserva como fallback. Sin `--surrender` el bot no se rinde (comportamiento actual). Sin `--fog` se asume `disable_fog=True` (comportamiento actual).
