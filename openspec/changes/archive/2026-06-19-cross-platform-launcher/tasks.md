## 1. Paquete instalable (editable install)

- [x] 1.1 Agregar `[build-system]` con `hatchling` a `pyproject.toml`
- [x] 1.2 Agregar `[tool.hatch.build.targets.wheel]` apuntando `packages = ["src"]` a `pyproject.toml`
- [x] 1.3 Verificar que `uv sync` instala el proyecto en editable (`uv run python -c "from src.bot.core import MyBot"` debe funcionar)

## 2. Script de lanzamiento cross-platform

- [x] 2.1 Agregar detección de SO con `platform.system()` en `scripts/run.py`
- [x] 2.2 Definir `SC2_DIR` y `MAPS_DIR` condicionales para Darwin y Windows
- [x] 2.3 Lanzar `RuntimeError` si el SO no es soportado
- [x] 2.4 Usar `MAPS_DIR` dinámico en `resolve_map()` en lugar del path hardcodeado actual
- [x] 2.5 Ejecutar `uv run python scripts/run.py` en macOS para verificar que el import funciona (debe fallar solo por falta de SC2, no por ModuleNotFoundError)

## 3. Script de mapas para Windows 11

- [x] 3.1 Crear `scripts/setup_maps.bat` con estructura: mensaje de inicio, creación de directorio, descarga, extracción, limpieza
- [x] 3.2 Implementar descarga con `curl` para `Ladder2019Season3.zip` y `Melee.zip`
- [x] 3.3 Implementar extracción con PowerShell usando `-ExecutionPolicy Bypass` y manejo de contraseña `iagreetotheeula` con `System.IO.Compression`
- [x] 3.4 Agregar limpieza de archivos temporales en `%TEMP%`
- [x] 3.5 Agregar mensajes de progreso y éxito con comando de verificación

## 4. Documentación

- [x] 4.1 Agregar sección de Windows 11 en README.md (español): requisitos, instalación, mapas, ejecución
- [x] 4.2 Agregar sección de Windows 11 en README.md (inglés): requirements, setup, maps, run
- [x] 4.3 Verificar que las instrucciones de macOS sigan siendo correctas tras los cambios

## 5. Verificación

- [x] 5.1 Ejecutar `uv run pytest` y confirmar que todos los tests pasan
- [x] 5.2 Verificar en macOS: `uv sync` → `./scripts/setup_maps.sh` → `uv run python scripts/run.py` flujo completo (fallo esperado solo si SC2 no está instalado)
