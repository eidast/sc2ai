# sc2ai

> De script a mente, paso a paso.

## Español

**sc2ai** es un proyecto recreativo y académico para construir un bot de StarCraft II que juega partidas completas. Empezamos con lógica programada y la arquitectura está diseñada para evolucionar hacia machine learning.

El bot juega **Protoss** con un estilo macro: expandir, producir sondas y ejército, y atacar cuando alcanza 200 de suministro.

### Requisitos

- **StarCraft II** instalado en macOS: `/Applications/StarCraft II/`
- **Python 3.9+** probado con 3.13
- **uv** para gestión de dependencias
- **Mapas** de ladder descargados en `/Applications/StarCraft II/Maps/`

### Instalación

```bash
git clone git@github.com:eidast/sc2ai.git
cd sc2ai
uv sync
```

### Mapas

Descarga los map packs oficiales de Blizzard o de [AI Arena](https://aiarena.net/wiki/maps/) y extráelos en:

```text
/Applications/StarCraft II/Maps/
```

También puedes usar el helper:

```bash
./scripts/setup_maps.sh
```

### Ejecutar

```bash
uv run python scripts/run.py
```

El bot juega Protoss contra la IA integrada de Blizzard (Terran, dificultad Media) en modo acelerado.

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
└── run.py        # Script de lanzamiento
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

- **StarCraft II** installed on macOS: `/Applications/StarCraft II/`
- **Python 3.9+** tested with 3.13
- **uv** for dependency management
- **Ladder maps** downloaded into `/Applications/StarCraft II/Maps/`

### Setup

```bash
git clone git@github.com:eidast/sc2ai.git
cd sc2ai
uv sync
```

### Maps

Download Blizzard's official map packs or maps from [AI Arena](https://aiarena.net/wiki/maps/) and extract them into:

```text
/Applications/StarCraft II/Maps/
```

You can also use the helper:

```bash
./scripts/setup_maps.sh
```

### Run

```bash
uv run python scripts/run.py
```

The bot plays Protoss against Blizzard's built-in AI (Terran, Medium difficulty) in accelerated mode.

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
└── run.py        # Launch script
```

### Roadmap

1. **Foundation**: scripted bot with basic macro
2. **Observation**: feature extraction and logging
3. **ML**: first model making decisions
4. **RL**: reinforcement learning with local replays

### License

MIT. See [LICENSE](LICENSE).
