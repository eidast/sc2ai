## Context

Actualmente el proyecto solo funciona en macOS porque:
- `scripts/run.py` asume `/Applications/StarCraft II/` como path de SC2
- `scripts/setup_maps.sh` es un script bash que usa `unzip -P` para mapas con contraseña
- El proyecto no está configurado como paquete Python instalable, lo que causa `ModuleNotFoundError: No module named 'src'`

El spec `project-foundation` existente declara que `from src.bot.core import MyBot` debe funcionar, pero no especifica **cómo** se logra (asume implícitamente que `PYTHONPATH` o `sys.path` están configurados).

## Goals / Non-Goals

**Goals:**
- Un solo `scripts/run.py` que funcione en macOS y Windows 11 sin cambios manuales
- `uv sync` debe dejar el proyecto en estado funcional (import `src` funciona, sin pasos extra)
- Windows 11 debe tener un script de setup de mapas que no requiera instalar herramientas adicionales
- La experiencia de setup debe ser: clonar → `uv sync` → script de mapas → `uv run python scripts/run.py`

**Non-Goals:**
- Linux — fuera de scope por ahora (aunque Darwin detection cubriría Linux si se agregan paths después)
- UI / instaladores gráficos
- Soporte para otras versiones de Windows (solo 11)
- Dockerización

## Decisions

### D1: Hatchling como build backend para editable install

**Decisión:** Agregar `[build-system]` con `hatchling` y `[tool.hatch.build.targets.wheel]` apuntando a `src/`.

**Alternativas consideradas:**
- `setuptools` — más verboso, requiere `setup.py` o `[tool.setuptools.packages.find]`, más pesado
- `flit` — buena opción pero hatchling es el default de `uv init` y más estándar en el ecosistema uv
- Manipular `sys.path` en `run.py` — frágil, no resuelve el problema para tests ni otros scripts

**Razón:** Hatchling es ligero, no requiere archivos extra, y es el backend recomendado por `uv`. Con `packages = ["src"]` basta.

### D2: `platform.system()` para detección de SO

**Decisión:** Un solo `scripts/run.py` que usa `platform.system()` (stdlib, sin dependencias) para detectar el SO y configurar paths.

**Mapeo:**
```python
if system == "Darwin":
    SC2_DIR = "/Applications/StarCraft II"
elif system == "Windows":
    SC2_DIR = r"C:\Program Files (x86)\StarCraft II"
else:
    raise RuntimeError(f"Unsupported OS: {system}")
```

**Alternativas consideradas:**
- Scripts separados (`run_macos.py`, `run_windows.py`) — duplicación de lógica del bot
- `os.name` — menos granular (solo `posix` vs `nt`, no distingue macOS de Linux)
- Variable de entorno `SC2_DIR` — requiere configuración manual del usuario, va contra el goal de "cero pasos extra"

### D3: `.bat` con PowerShell embebido para extracción de zips con contraseña

**Decisión:** `scripts/setup_maps.bat` usa `curl` (incluido en Windows 10+) para descargar y PowerShell para extraer. La extracción se hace con `[System.IO.Compression.ZipFile]` más un wrapper que maneja la contraseña usando `System.IO.Compression.ZipArchive` con `ZipArchiveMode.Read` y entrada con contraseña.

**Alternativas consideradas:**
- 7-Zip como dependencia — requeriría instalación previa
- Python script (`setup_maps.py`) — cross-platform pero el usuario pidió `.bat`
- Extracción manual documentada en README — peor experiencia

**Razón:** La combinación curl + PowerShell está disponible out-of-the-box en Windows 11. No requiere que el usuario instale nada. La contraseña se maneja con clases de .NET accesibles desde PowerShell.

### D4: Estructura de paths centralizada en `run.py`

**Decisión:** El script de launch define paths de SC2 y mapas como constantes condicionales. Los scripts de setup de mapas también usan paths condicionales (hardcodeados por SO en cada script).

**Alternativa considerada:** Archivo de configuración `.env` o `config.json` — agrega complejidad innecesaria para solo 2 paths.

## Risks / Trade-offs

- **Riesgo:** Usuario instala SC2 en un path no estándar (ej. otro disco en Windows) → **Mitigación:** Documentar paths esperados en README; en el futuro se puede agregar soporte para variable de entorno `SC2_DIR` como override.
- **Riesgo:** `hatchling` agrega una dependencia de build → **Mitigación:** Es mínimo (~2MB), solo se usa al hacer `uv sync`, no en runtime del bot.
- **Riesgo:** El `.bat` con PowerShell embebido puede fallar si la política de ejecución de PowerShell está restringida → **Mitigación:** Usar `powershell -ExecutionPolicy Bypass -Command "..."` en el `.bat`.
- **Trade-off:** Paths hardcodeados por SO en lugar de auto-detección → Es más simple y predecible. La auto-detección (buscar `StarCraft II.exe` en el disco) sería lenta y frágil.
