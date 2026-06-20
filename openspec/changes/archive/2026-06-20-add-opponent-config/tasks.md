## 1. CLI flags

- [x] 1.1 Añadir constantes `DIFFICULTY_CHOICES` y `RACE_CHOICES` en `scripts/run.py` con los valores permitidos (excluyendo cheats)
- [x] 1.2 Añadir `--difficulty` a argparse con `choices=DIFFICULTY_CHOICES`, `default="Medium"`
- [x] 1.3 Añadir `--opponent-race` a argparse con `choices=RACE_CHOICES`, `default="Terran"`
- [x] 1.4 Añadir `--opponents` a argparse con `type=int`, `default=1`, validacion de rango 1-4

## 2. Dynamic opponent construction

- [x] 2.1 Construir lista de `Computer` dinamicamente en `main()` usando los flags: `for _ in range(args.opponents)` mapeando `getattr(Difficulty, ...)` y `getattr(Race, ...)`
- [x] 2.2 Pasar `args.difficulty`, `args.opponent_race`, `args.opponents` a `MyBot(...)` como kwargs

## 3. Bot receives opponent config

- [x] 3.1 Añadir parametros `opponent_difficulty: str`, `opponent_race: str`, `opponent_count: int` al `__init__` de `MyBot` con defaults `"Medium"`, `"Terran"`, `1`
- [x] 3.2 Reemplazar `bot_info["opponent_difficulty"] = "Medium"` por `self.opponent_difficulty` en `on_end()`
- [x] 3.3 Reemplazar `bot_info["opponent_race"] = ...` por `self.opponent_race` en `on_end()`

## 4. Tests

- [x] 4.1 Test: argparse acepta valores validos y rechaza invalidos para `--difficulty`
- [x] 4.2 Test: argparse acepta valores validos y rechaza invalidos para `--opponent-race`
- [x] 4.3 Test: argparse acepta `--opponents` en rango 1-4 y rechaza fuera de rango
- [x] 4.4 Test: defaults de los tres flags nuevos coinciden con el comportamiento actual
- [x] 4.5 Test: `MyBot` almacena y expone `opponent_difficulty`, `opponent_race`, `opponent_count`

## 5. Verification

- [x] 5.1 Ejecutar `uv run pytest` — todos los tests pasan
- [x] 5.2 Verificar que `uv run python scripts/run.py --help` muestra los nuevos flags
