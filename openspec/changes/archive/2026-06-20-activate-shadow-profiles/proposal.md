## Why

El modo `ml_shadow` existe como placeholder pero no produce predicciones reales — `shadow_prediction` siempre es `null` en `decisions.jsonl`. Esto impide cualquier A/B testing o comparación entre estrategias. Hay que activarlo conectándolo a los perfiles de estrategia YAML ya existentes (`stargate_open`, `robo_open`, `fast_expand`), que correrán en paralelo como "sombras" sin afectar el gameplay.

## What Changes

- **Multi-shadow engine**: `ml_shadow` acepta 1+ perfiles de estrategia como `--shadow-profile`. Cada uno corre su propio `BiasCalculator` + `PriorityEngine` independiente, registrando predicciones en `decisions.jsonl` sin controlar el juego.
- **Shadow predictions array**: `shadow_prediction` (singular, null) pasa a ser `shadow_predictions` (plural, array) en el JSONL. Cada entrada incluye `profile` y `recommended_action`. **BREAKING** en el formato de `decisions.jsonl`.
- **Fix scout decay duplication**: `BiasCalculator._apply_scout_decay()` muta `scout_metadata` in-place. Con múltiples calculadoras, cada una re-aplica decay sobre datos ya degradados. Se elimina este método — el decay ya lo aplica `ScoutMetadata.apply_decay()` en `on_step`.
- **CLI validation**: `--policy-mode ml_shadow` sin `--shadow-profile` produce error con lista de perfiles disponibles. `--shadow-profile` usa `action="append"` para soportar múltiples valores.

## Capabilities

### New Capabilities

- `shadow-profile-engine`: Carga y ejecución de múltiples perfiles de estrategia como sombras paralelas durante el juego. Cada shadow evalúa sus propias fórmulas de prioridad con su propio vector de sesgos, produciendo predicciones independientes registradas en JSONL.

### Modified Capabilities

- `policy-shadow-telemetry`: El campo `shadow_prediction` (singular/null) cambia a `shadow_predictions` (array). Las predicciones ahora incluyen `profile` y `recommended_action`. Se añade validación de perfil requerido en `ml_shadow`.

## Impact

- `src/bot/core.py`: Nuevo atributo `shadow_profiles`, arrays de `_shadow_bias_calculators` y `_shadow_priority_engines`, `_last_shadow_predictions`. Evaluación en `on_step`.
- `src/strategies/bias_calculator.py`: Eliminación de `_apply_scout_decay()`.
- `scripts/run.py`: `--shadow-profile` con `action="append"`, validación post-parse.
- `openspec/specs/policy-shadow-telemetry/spec.md`: Actualización de requisitos de shadow prediction.
- Tests: `test_early_game.py`, `test_bot_logging.py`, `test_run_script.py`, `test_bias_calculator.py`.
