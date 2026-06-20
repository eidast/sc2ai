## Context

Actualmente `scripts/run.py` construye el oponente con valores hardcodeados:
```python
Computer(Race.Terran, Difficulty.Medium)
```

`src/bot/core.py` también hardcodea `"opponent_difficulty": "Medium"` en `bot_info` para el reporte. No hay forma de cambiar la dificultad, raza, o número de oponentes sin editar código.

El sistema de reportes (`src/ml/report.py`) ya lee `opponent_race` y `opponent_difficulty` de `bot_info` de forma genérica — solo falta que quien lo provee (el bot) reciba los valores reales.

## Goals / Non-Goals

**Goals:**
- Permitir configurar dificultad, raza, y número de oponentes desde la CLI
- El bot refleja la configuración real en el reporte de partida
- Defaults mantienen el comportamiento actual (Terran, Medium, 1)
- Validación clara de valores inválidos

**Non-Goals:**
- Diferente dificultad/raza por oponente (todos comparten la misma config)
- Soporte para dificultades con cheat (`CheatVision`, `CheatMoney`, `CheatInsane`)
- Interfaz gráfica o archivo de configuración (solo CLI)

## Decisions

### 1. Flags compartidos para todos los oponentes

**Decisión**: `--difficulty`, `--opponent-race`, `--opponents` aplican a todos los oponentes por igual.

**Alternativa considerada**: Sintaxis `--opponents "Zerg:Hard,Terran:Medium"` para oponentes heterogéneos. Descartada por complejidad de parsing y porque el caso de uso primario es "jugar" (no benchmarks con mezclas exóticas).

**Si en el futuro se necesita**: Se puede añadir una sintaxis extendida sin romper la actual.

### 2. Mapeo de strings a enums

**Decisión**: `argparse` con `choices` restringido a los valores válidos. El mapeo se hace con `getattr(Difficulty, value)` y `getattr(Race, value)`.

```python
DIFFICULTY_CHOICES = ["VeryEasy","Easy","Medium","MediumHard","Hard","Harder","VeryHard"]
RACE_CHOICES = ["Terran","Zerg","Protoss","Random"]
```

**Alternativa considerada**: Aceptar cualquier string y validar después. Descartada — argparse con `choices` da mensajes de error automáticos y shells pueden autocompletar.

### 3. Paso de configuración al bot

**Decisión**: Añadir tres parámetros al constructor de `MyBot`:

```python
def __init__(self, ...,
             opponent_difficulty: str = "Medium",
             opponent_race: str = "Terran",
             opponent_count: int = 1):
```

El bot los usa solo para `bot_info` en `on_end()`. La lógica de juego no consulta esta metadata (aunque queda disponible para uso futuro).

### 4. Construcción dinámica de oponentes en run_game

**Decisión**: En `main()`, construir una lista de `Computer` según `args.opponents`:

```python
opponents = [
    Computer(Race[args.opponent_race], Difficulty[args.difficulty])
    for _ in range(args.opponents)
]
players = [Bot(Race.Protoss, MyBot(...), fullscreen=True)] + opponents
```

### 5. Validación del número de oponentes

**Decisión**: `type=int` con validación de rango vía `choices=range(1,5)` o validación manual en `main()`. Límite 4 para evitar partidas absurdamente lentas.

## Risks / Trade-offs

- **El bot desconoce la raza real si se usa `Random`**: `self.enemy_race` se resuelve en runtime; el `bot_info` usa el valor del flag. Si el flag es `Random`, el reporte dirá literalmente `Random` en vez de la raza descubierta. → Aceptable; es metadata de configuración, no de la partida en sí.
- **Múltiples oponentes con `--realtime` puede ser lento**: Sin mitigación automática; es elección del usuario.
- **El test de `main()` requiere mock de `run_game`**: Los tests actuales no cubren `main()`. Se puede testear argparse aislando el parsing.
