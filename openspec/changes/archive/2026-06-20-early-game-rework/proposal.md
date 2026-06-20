## Why

El bot Protoss actual fracasa repetidamente contra Terran Hard porque **nunca construye un Gateway** ni unidades de producción, acumulando 3500+ minerales sin ejercito. La causa raiz es que `manage_tech` tiene un early return que prioriza estructuras tech (Forge, Robo) sobre el Gateway, y no existe una secuencia temprana obligatoria. Esto hace que el bot quede en un estado irrecuperable sin produccion militar. 2 de 3 partidas Hard resultaron en derrota por este patron.

## What Changes

- **Nuevo** `manage_early_game()` con secuencia fija obligatoria (Pylon → Gateway → Cyber Core → Warp Gate) durante los primeros ~90s de juego, con reintentos y logging de diagnostico
- **Reestructurar** `manage_tech()` para que Gateway SIEMPRE se construya antes de cualquier estructura tech, independientemente de lo que recomiende el strategy engine
- **Modificar** formulas YAML (`standard_macro.yaml`, `robo_open.yaml`) con prerequisitos explicitos: `has_structure('GATEWAY')` para Forge, `has_structure('CYBERNETICSCORE')` para Robo/Stargate
- **Modificar** `manage_gas()` para limitarse a 1 Assimilator antes de tener Gateway
- **Modificar** `manage_expansion()` con trigger por mineral banking (>400 minerals → expandir)
- **Agregar** `_build_if_able()` como helper reutilizable con logging de exito/fallo (motivo: cant afford, no worker, placement failed)
- **Agregar** worker check antes de cada `self.build()` para evitar fallos silenciosos

## Capabilities

### New Capabilities
- `early-game-build-order`: Secuencia fija obligatoria de construccion temprana (Pylon → Gateway → Cyber Core → Warp Gate) con reintentos, timeouts, y logging de diagnostico. Garantiza que el bot siempre tenga produccion militar basica.

### Modified Capabilities
- `bot-gameplay`: La seccion "Tech progression" cambia para reflejar que el Gateway se construye ANTES de cualquier otra estructura tech (no despues de un Gateway completado cualquiera). El build order temprano es ahora deterministico, no depende del strategy engine.
- `gas-economy`: El requisito "Only one assimilator is built per step" se complementa con "maximo 1 Assimilator antes de tener Gateway" para evitar que `manage_gas` compita por workers con la construccion del Gateway.
- `strategic-decision`: Las formulas de prioridad en los perfiles YAML ahora incluyen prerequisitos de estructura (`has_structure('GATEWAY')`, `has_structure('CYBERNETICSCORE')`) para que el engine no recomiende estructuras sin la cadena de produccion previa.

## Impact

- `src/bot/core.py`: Metodos nuevos (`manage_early_game`, `_build_if_able`), reescritura de `manage_tech`, modificaciones a `manage_gas`, `manage_expansion`
- `src/data/strategies/protoss/standard_macro.yaml`: Formulas con prerequisitos
- `src/data/strategies/protoss/robo_open.yaml`: Formulas con prerequisitos
- `src/bot/strategy.py`: Constantes nuevas (EARLY_GAME_PHASES, timeouts)
- Tests: `test_early_game.py` (nuevo), `test_manage_tech.py` (modificado)
