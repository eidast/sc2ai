## Why

El modo `ml_shadow` ya produce predicciones reales de múltiples perfiles en `decisions.jsonl`, pero no hay herramientas para analizar esos datos. Sin análisis, la comparación entre perfiles es manual e ineficiente. Además, el motor de prioridad tiene dos limitaciones: recomienda unidades sin verificar prerequisitos del tech tree (ej. COLOSSUS sin ROBOTICSBAY), y salta entre targets sin inercia (STALKER → VOIDRAY → STALKER en steps consecutivos), generando recomendaciones incoherentes.

## What Changes

- **Script de análisis post-partido**: `scripts/analyze_shadows.py` que lee `decisions.jsonl` + `features.jsonl` y genera métricas comparativas entre heurística y shadows (agreement matrix, action distribution, bias evolution, timeline).
- **Tech tree awareness**: `PriorityEngine._is_reachable()` verifica que las estructuras requeridas existan antes de recomendar una unidad/upgrade. Los perfiles YAML pueden declarar `requires` por fórmula.
- **Action momentum**: `PriorityEngine.evaluate()` aplica un bonus de continuidad (+15%) cuando la acción recomendada coincide con la del step anterior, evitando saltos incoherentes.

## Capabilities

### New Capabilities

- `shadow-analysis-tool`: Script CLI que lee los JSONL de un match y produce métricas comparativas multi-perfil (agreement, distribución, evolución de sesgos, timeline).
- `tech-tree-awareness`: El `PriorityEngine` filtra acciones cuyas estructuras requeridas no existen. Los perfiles YAML declaran `requires` opcional por fórmula.
- `action-momentum`: El `PriorityEngine` aplica un multiplicador de continuidad cuando la acción candidata coincide con la acción del step anterior.

### Modified Capabilities

- `shadow-profile-engine`: El script de análisis consume los `shadow_predictions` generados por esta capability.

## Impact

- `scripts/analyze_shadows.py`: Nuevo script, ~150 LOC. Dependencia: solo stdlib (json, csv, argparse).
- `src/strategies/priority_engine.py`: `_is_reachable()` ampliado con chequeo de `requires`. `evaluate()` con parámetro `prev_action` y bonus de momentum.
- `src/strategies/types.py`: `StrategyProfile.priority_formulas` extiende su schema para aceptar `requires` y `max_count`.
- `src/strategies/loader.py`: `_parse()` adaptado al nuevo schema con `requires`.
- `src/bot/core.py`: Pasa `self._last_action` como `prev_action` al `PriorityEngine.evaluate()`.
- `src/data/strategies/protoss/*.yaml`: Se agregan campos `requires` a fórmulas que dependen de estructuras.
