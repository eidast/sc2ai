# Setup Guide — macOS

## Requisitos previos

1. **StarCraft II** instalado desde [Battle.net](https://starcraft2.com/)
   - Ubicación default: `/Applications/StarCraft II/`
   - La versión Starter (gratuita) funciona

2. **Python 3.9+**
   ```bash
   python3 --version  # Debe ser >= 3.9
   ```

3. **uv** (gestor de paquetes)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Instalación del proyecto

```bash
git clone git@github.com:eidast/sc2ai.git
cd sc2ai
uv sync
```

Esto instala `burnysc2` y todas sus dependencias en un entorno virtual `.venv/`.

## Mapas

Sin mapas el bot no puede jugar. Descarga los map packs oficiales:

```bash
# Opción 1: Mapas del ladder de Blizzard
# Visita: https://github.com/Blizzard/s2client-proto#downloads
# Password: iagreetotheeula
# Descarga Ladder2019Season3.zip (o el más reciente)
# Extrae en: /Applications/StarCraft II/Maps/

# Opción 2: Mapas de AI Arena
# Visita: https://aiarena.net/wiki/maps/
```

Estructura esperada después de extraer:
```
/Applications/StarCraft II/Maps/
├── Ladder2019Season3/
│   ├── AcropolisLE.SC2Map
│   ├── ThunderbirdLE.SC2Map
│   └── ...
```

## Verificar que todo funciona

```bash
# Verificar que python-sc2 encuentra los mapas
uv run python -c "from sc2 import maps; print(maps.get('Acropolis'))"

# Ejecutar una partida
uv run python scripts/run.py
```

La primera ejecución puede tardar mientras SC2 carga. El juego se abre en una ventana y corre en modo acelerado (`realtime=False`). Una partida típica dura entre 2 y 5 minutos en este modo.

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `SC2 not found` | Verifica que SC2 está en `/Applications/StarCraft II/` |
| `Map not found` | Descarga y extrae los mapas en la carpeta correcta |
| `Connection refused` | Asegúrate de que SC2 no está ya abierto |
| Python version error | Usa `pyenv` para cambiar a Python 3.9-3.12 |
