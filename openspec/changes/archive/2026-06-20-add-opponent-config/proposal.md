## Why

El runner actual tiene la configuración del oponente hardcodeada (`Computer(Race.Terran, Difficulty.Medium)`, un solo oponente). Para probar el bot contra diferentes razas, dificultades, o múltiples oponentes hay que editar el código a mano. Esto frena la experimentación y el disfrute del juego.

## What Changes

- Nuevos flags CLI en `scripts/run.py`: `--difficulty`, `--opponent-race`, `--opponents`
- `MyBot.__init__` recibe `opponent_difficulty`, `opponent_race`, `opponent_count` para usarlos en el reporte de partida
- `bot_info` en `on_end()` usa los valores reales en vez de strings hardcodeados (`"Medium"`, `"Terran"`)
- `run_game` construye `Computer(...)` dinámicamente según los flags
- El README ya documenta las opciones

## Capabilities

### New Capabilities
- `opponent-config`: configuración de oponentes vía CLI — dificultad, raza, y cantidad de oponentes, con defaults sensatos y validación de valores.

### Modified Capabilities
- `cross-platform-launcher`: se añaden los nuevos flags al script `run.py` y la lógica de construcción de oponentes en `run_game`.

## Impact

- `scripts/run.py`: nuevos argumentos argparse, construcción dinámica de `Computer`
- `src/bot/core.py`: nuevos parámetros en `__init__`, `bot_info` dinámico en `on_end`
- `src/ml/report.py`: sin cambios (ya lee `bot_info` genéricamente)
- `tests/test_run_script.py`: nuevos tests de CLI
- `README.md`: ya actualizado con la documentación de flags
