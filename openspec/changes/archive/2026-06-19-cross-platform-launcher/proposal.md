## Why

El script de lanzamiento `scripts/run.py` no funciona — `ModuleNotFoundError: No module named 'src'` — porque el proyecto no está configurado como paquete Python instalable. Además, todos los paths están hardcodeados para macOS, haciendo imposible ejecutar la simulación en Windows 11. Esto frena a cualquier colaborador o al mismo autor si cambia de máquina.

## What Changes

- **Configurar `pyproject.toml`** con `[build-system]` y `[tool.hatch.build.targets.wheel]` para que `uv sync` instale el proyecto en modo editable. Esto hace que `from src.bot.core import MyBot` funcione sin manipular `sys.path`.
- **Modificar `scripts/run.py`** para detectar el sistema operativo automáticamente (`platform.system()`) y configurar los paths de StarCraft II y mapas para macOS (Darwin) y Windows según corresponda.
- **Crear `scripts/setup_maps.bat`** — script batch para Windows 11 que descarga y extrae los map packs de Blizzard. Usa PowerShell embebido para manejar zips con contraseña (`iagreetotheeula`), sin requerir herramientas externas.
- **Actualizar `README.md`** con instrucciones de instalación y ejecución para Windows 11 (en español e inglés).

## Capabilities

### New Capabilities

- `cross-platform-launcher`: Un solo script `scripts/run.py` que detecta el SO y configura paths de SC2 para macOS y Windows 11 automáticamente.
- `windows-map-setup`: Script `scripts/setup_maps.bat` para Windows 11 que descarga y extrae los map packs oficiales usando curl + PowerShell (maneja zips con contraseña sin dependencias externas).

### Modified Capabilities

- `project-foundation`: El requirement "Module imports work" (escenario línea 42-43 del spec) ahora debe reflejar que el proyecto se instala en modo editable vía `uv sync` + `[build-system]`, no por manipulación manual del path.

## Impact

- `pyproject.toml` — se agregan secciones `[build-system]` y `[tool.hatch.build]`
- `scripts/run.py` — se reescribe con detección de SO y paths dinámicos
- `scripts/setup_maps.bat` — nuevo archivo
- `README.md` — se agregan secciones de Windows en ambas lenguas
- `.gitignore` — verificar que `.bat` no esté excluido (no debería)
