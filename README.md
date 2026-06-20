# sc2ai

> De script a mente, paso a paso.

**sc2ai** es un proyecto recreativo y académico para construir un bot de StarCraft II que juega partidas completas. Empezamos con lógica programada (scripted) y la arquitectura está diseñada para evolucionar hacia machine learning.

El bot juega **Protoss** con un estilo macro: expandir, producir sondas y ejército, y atacar cuando alcanza 200 de suministro.

---

> From script to mind, step by step.

**sc2ai** is a recreational and academic project to build a StarCraft II bot that plays full matches. We start with scripted logic, and the architecture is designed to evolve into machine learning.

The bot plays **Protoss** with a macro style: expand, produce probes and army, and attack when maxed at 200 supply.

---

## Requisitos / Requirements

- **StarCraft II** instalado (macOS: `/Applications/StarCraft II/`)
- **Python 3.9+** (probado con 3.13)
- **uv** para gestión de dependencias
- **Mapas** de ladder descargados en `Maps/`

## Instalación / Setup

```bash
git clone git@github.com:eidast/sc2ai.git
cd sc2ai
uv sync
```

## Mapas / Maps

Descarga los map packs oficiales de Blizzard o de [AI Arena](https://aiarena.net/wiki/maps/) y extráelos en:

```
/Applications/StarCraft II/Maps/
```

## Ejecutar / Run

```bash
uv run python scripts/run.py
```

El bot juega Protoss contra la IA integrada de Blizzard (Terran, dificultad Media) en modo acelerado.

---

## Estructura / Structure

```
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

## Hoja de ruta / Roadmap

1. **Fundación** — Bot scripted con macro básico
2. **Observación** — Extracción de features y logging
3. **ML** — Primer modelo tomando decisiones
4. **RL** — Reinforcement learning con replays propios

## Licencia / License

MIT — Ver [LICENSE](LICENSE)
