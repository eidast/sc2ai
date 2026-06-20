## Why

El bot actual toma todas sus decisiones mediante funciones deterministas sin contexto estratégico (monoriel). Cada `manage_*` opera en aislamiento, el FSM de `decision.py` usa umbrales fijos, y no existe capacidad de adaptarse dinámicamente al scouting enemigo ni de manejar múltiples estilos de juego. Este cambio introduce un motor estratégico basado en utility scoring — el enfoque usado por la industria de videojuegos (The Sims, Civilization, F.E.A.R., Killzone 2) desde hace 20 años — que reemplaza decisiones discretas por un campo de fuerzas continuo donde cada acción tiene una utilidad calculada y la mejor gana, permitiendo transiciones graduales, scouting como driver principal, y escalabilidad multi-raza.

## What Changes

- **REEMPLAZA** el FSM `decision.py` por un `BiasCalculator` que convierte scouting, métricas e historial en biases continuos [0.0–1.0] — no más estados discretos (DEFEND/ATTACK/RECOVER), sino una superficie continua de preferencias estratégicas
- **AGREGA** un `PriorityEngine` que evalúa cada step la utilidad de todas las acciones posibles (construir unidades, edificios, upgrades, expandir) y selecciona la de mayor score — eliminando la necesidad de build orders rígidos
- **AGREGA** perfiles de estrategia en YAML que definen `initial_biases`, `scouting_adjustments` y `priority_formulas` — cada estrategia no es un camino fijo, sino una configuración de "campo gravitacional" que inclina las decisiones
- **MODIFICA** todas las funciones `manage_*` para que deleguen la selección de objetivos al `PriorityEngine` en lugar de decidir independientemente — dejan de ser autónomas y pasan a ser ejecutoras
- **AGREGA** soporte para inferencia de scouting con decaimiento temporal — la información de unidades enemigas pierde confianza con el tiempo sin re-scoutear
- Prepara la arquitectura para ML futuro: el engine aprende parámetros (no decide acciones), manteniendo interpretabilidad

## Capabilities

### New Capabilities

- `bias-calculator`: Convierte datos de scouting (composición enemiga, edificios, eco inferido), métricas internas (army ratio, eco, supply) e historial de partidas en biases continuos. Aplica decaimiento temporal a la info de scouting. Permite configurar `bias_speed` global y por fase de juego.
- `priority-engine`: Evalúa cada step la utilidad de cada acción alcanzable (construir unidades, estructuras, upgrades, expandir) usando fórmulas definidas en los perfiles YAML. Selecciona la acción de mayor score y delega su ejecución a la función `manage_*` correspondiente.
- `strategy-yaml-profiles`: Define el formato YAML para perfiles de estrategia: `initial_biases`, `scouting_adjustments` (cómo el scouting modifica los biases), `priority_formulas` (ecuaciones de utilidad por acción), y `meta_params` (bias_speed, decay_rate). Escalable a múltiples razas sin cambios de código.
- `strategy-delegation`: Las funciones `manage_*` existentes se refactorizan para consultar al `PriorityEngine` por el objetivo actual (qué construir, qué expandir, qué upgrade) en lugar de decidir autónomamente. Mantienen responsabilidad sobre el cómo (pathfinding, placement, micro).

### Modified Capabilities

- `strategic-decision`: El FSM actual (`decision.py`) se subordina al utility engine. Los estados DEFEND/ATTACK/RECOVER/SURRENDER/WON dejan de ser el motor principal de decisiones tácticas y pasan a ser outputs de alto nivel para logging y reportes, o condiciones de freno (surrender, victory).
- `observation-pipeline`: Se agregan features: `scout_age` (tiempo desde último scouting por tipo de unidad), `building_inference` (edificios enemigos vistos que sugieren composición futura), `eco_inference` (estimación de eco enemiga basada en bases y gas vistos).
- `scout-behavior`: El scouting ahora registra metadata de certeza y timestamp por tipo de unidad observada, no solo waypoints y retirada por HP.
- `upgrade-strategy`: Las prioridades de upgrades se definen en los perfiles YAML con fórmulas de utilidad, reemplazando la lógica hardcodeada de `UPGRADE_ORDER`.

## Impact

- `src/bot/decision.py`: se subsume bajo el utility engine; los estados del FSM quedan como outputs de logging
- `src/bot/core.py`: `on_step` integra `PriorityEngine` antes del bloque `manage_*`; `manage_*` reciben contexto estratégico
- `src/bot/upgrades.py`: lógica reemplazada por fórmulas de utilidad en perfiles YAML
- `src/ml/observation.py`: nuevas features de scouting con metadata temporal
- `src/bot/scout.py`: registro de certeza y timestamp por observación
- Nuevo directorio `src/strategies/` con `bias_calculator.py`, `priority_engine.py`, `loader.py` y perfiles YAML en `strategies/protoss/`
- Nuevo directorio `src/data/strategies/` para los archivos YAML de perfiles
- No se afectan: `manage_probes`, `manage_pylons`, `manage_gas`, `manage_expansion`, `manage_defense`, `manage_attack` (ejecución del cómo), `replay`, `logger`, `report`
