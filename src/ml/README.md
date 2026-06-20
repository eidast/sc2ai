# ML — Machine Learning

## Intención futura

Este directorio contiene el puente hacia machine learning. Hoy solo tenemos `observation.py` con extracción de features del estado del juego. Mañana:

- **Entrenamiento**: Usar replays propios como datos de entrenamiento
- **Inferencia**: Reemplazar la lógica scripted de `src/bot/core.py` con predicciones de un modelo
- **RL**: Implementar un loop de reinforcement learning usando python-sc2 como entorno

## Arquitectura prevista

```
on_step():
    1. features = extract_features(game_state)   ← hoy: logging
    2. action = model.predict(features)           ← futuro: ML decide
    3. execute(action)
    4. save_to_replay_buffer(features, action)    ← futuro: entrenar
```

La interfaz `extract_features()` es el contrato: lo que extraemos hoy para logging es exactamente lo que el modelo consumirá mañana. No habrá que refactorizar, solo enchufar.
