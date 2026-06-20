# sc2ai

> De script a mente, paso a paso.

## Español

**sc2ai** es un proyecto recreativo y académico para construir un bot de StarCraft II que juega partidas completas. Empezamos con lógica programada y la arquitectura está diseñada para evolucionar hacia machine learning.

El bot juega **Protoss** con un estilo macro: expandir, producir sondas y ejército, y atacar cuando alcanza 200 de suministro.

### Requisitos

- **StarCraft II** instalado (la edición gratuita Starter Edition funciona):
  - macOS: `/Applications/StarCraft II/`
  - Windows 11: `C:\Program Files (x86)\StarCraft II\`
- **Python 3.9+** probado con 3.13
- **uv** para gestión de dependencias

### Instalación

```bash
git clone git@github.com:eidast/sc2ai.git
cd sc2ai
uv sync
```

`uv sync` instala las dependencias y configura el proyecto en modo editable — no necesitás pasos extra.

### Mapas

Descargá los map packs oficiales de Blizzard o de [AI Arena](https://aiarena.net/wiki/maps/).

Usá el helper según tu sistema:

**macOS:**
```bash
./scripts/setup_maps.sh
```

**Windows 11:**
```batch
scripts\setup_maps.bat
```

Los mapas se instalan automáticamente en el directorio de StarCraft II de tu sistema.

### Ejecutar

```bash
uv run python scripts/run.py
```

El script detecta automáticamente si estás en macOS o Windows y configura los paths correctos. El bot juega Protoss contra la IA integrada de Blizzard (Terran, dificultad Media) en modo acelerado.

#### Opciones de línea de comandos

| Flag | Default | Descripción |
|---|---|---|
| `--map` | `AcropolisLE` | Nombre del mapa o `random` para selección aleatoria |
| `--realtime` | (desactivado) | Velocidad normal con renderizado (por defecto: acelerado) |
| `--surrender` | (desactivado) | Rendición estratégica cuando la victoria es matemáticamente imposible |
| `--fog` | (desactivado) | Activar niebla de guerra (por defecto: visibilidad completa) |
| `--difficulty` | `Medium` | Dificultad de la IA enemiga: `VeryEasy`, `Easy`, `Medium`, `MediumHard`, `Hard`, `Harder`, `VeryHard` |
| `--opponent-race` | `Terran` | Raza del oponente: `Terran`, `Zerg`, `Protoss`, `Random` |
| `--opponents` | `1` | Número de oponentes (1–4). Todos comparten la misma dificultad y raza. |

Ejemplos:

```bash
# Contra Zerg en dificultad Hard con niebla de guerra
uv run python scripts/run.py --opponent-race Zerg --difficulty Hard --fog

# 1v2 contra Terran VeryHard con rendición automática
uv run python scripts/run.py --difficulty VeryHard --opponents 2 --surrender

# Partida en tiempo real con mapa aleatorio
uv run python scripts/run.py --map random --realtime
```

### Estructura

```text
src/
├── bot/          # Lógica del bot (extiende BotAI)
├── ml/           # Extracción de features, futuro ML
└── utils/        # Logging, replays
docs/
├── bitacora/     # Diario del proyecto (ES)
└── setup.md      # Guía de instalación detallada
scripts/
├── run.py        # Script de lanzamiento (cross-platform)
├── setup_maps.sh # Instalador de mapas (macOS)
└── setup_maps.bat# Instalador de mapas (Windows)
```

### Hoja de ruta

1. **Fundación**: bot scripted con macro básico
2. **Observación**: extracción de features y logging
3. **ML**: primer modelo tomando decisiones
4. **RL**: reinforcement learning con replays propios

### Licencia

MIT. Ver [LICENSE](LICENSE).

---

## English

> From script to mind, step by step.

**sc2ai** is a recreational and academic project to build a StarCraft II bot that plays full matches. We start with scripted logic, and the architecture is designed to evolve into machine learning.

The bot plays **Protoss** with a macro style: expand, produce probes and army, and attack when maxed at 200 supply.

### Requirements

- **StarCraft II** installed (the free Starter Edition works):
  - macOS: `/Applications/StarCraft II/`
  - Windows 11: `C:\Program Files (x86)\StarCraft II\`
- **Python 3.9+** tested with 3.13
- **uv** for dependency management

### Setup

```bash
git clone git@github.com:eidast/sc2ai.git
cd sc2ai
uv sync
```

`uv sync` installs dependencies and sets up the project in editable mode — no extra steps needed.

### Maps

Download Blizzard's official map packs or maps from [AI Arena](https://aiarena.net/wiki/maps/).

Use the helper for your system:

**macOS:**
```bash
./scripts/setup_maps.sh
```

**Windows 11:**
```batch
scripts\setup_maps.bat
```

Maps are installed automatically in your system's StarCraft II directory.

### Run

```bash
uv run python scripts/run.py
```

The script auto-detects whether you're on macOS or Windows and configures the correct paths. The bot plays Protoss against Blizzard's built-in AI (Terran, Medium difficulty) in accelerated mode.

#### CLI options

| Flag | Default | Description |
|---|---|---|
| `--map` | `AcropolisLE` | Map name or `random` for random selection |
| `--realtime` | (disabled) | Normal speed with rendering (default: accelerated) |
| `--surrender` | (disabled) | Strategic surrender when victory is mathematically impossible |
| `--fog` | (disabled) | Enable fog of war (default: full visibility) |
| `--difficulty` | `Medium` | Enemy AI difficulty: `VeryEasy`, `Easy`, `Medium`, `MediumHard`, `Hard`, `Harder`, `VeryHard` |
| `--opponent-race` | `Terran` | Opponent race: `Terran`, `Zerg`, `Protoss`, `Random` |
| `--opponents` | `1` | Number of opponents (1–4). All share the same difficulty and race. |

Examples:

```bash
# Against Zerg on Hard difficulty with fog of war
uv run python scripts/run.py --opponent-race Zerg --difficulty Hard --fog

# 1v2 against Terran VeryHard with auto-surrender
uv run python scripts/run.py --difficulty VeryHard --opponents 2 --surrender

# Real-time match on a random map
uv run python scripts/run.py --map random --realtime
```

### Structure

```text
src/
├── bot/          # Bot logic (extends BotAI)
├── ml/           # Feature extraction, future ML
└── utils/        # Logging, replays
docs/
├── bitacora/     # Project journal (ES)
└── setup.md      # Detailed setup guide
scripts/
├── run.py        # Launch script (cross-platform)
├── setup_maps.sh # Map installer (macOS)
└── setup_maps.bat# Map installer (Windows)
```

### Roadmap

1. **Foundation**: scripted bot with basic macro
2. **Observation**: feature extraction and logging
3. **ML**: first model making decisions
4. **RL**: reinforcement learning with local replays

### License

MIT. See [LICENSE](LICENSE).
