## ADDED Requirements

### Requirement: Script de lanzamiento detecta el sistema operativo
El sistema SHALL incluir un script `scripts/run.py` que detecta automáticamente el sistema operativo usando `platform.system()` y configura los paths de StarCraft II y directorio de mapas en función del SO detectado.

#### Scenario: Ejecución en macOS
- **WHEN** el script se ejecuta en macOS (Darwin)
- **THEN** `SC2_DIR` SHALL ser `/Applications/StarCraft II` y `MAPS_DIR` SHALL ser `/Applications/StarCraft II/Maps`

#### Scenario: Ejecución en Windows 11
- **WHEN** el script se ejecuta en Windows
- **THEN** `SC2_DIR` SHALL ser `C:\Program Files (x86)\StarCraft II` y `MAPS_DIR` SHALL ser `C:\Program Files (x86)\StarCraft II\Maps`

#### Scenario: Sistema operativo no soportado
- **WHEN** el script se ejecuta en un SO que no es Darwin ni Windows
- **THEN** el script SHALL lanzar `RuntimeError` con un mensaje descriptivo indicando el SO detectado

### Requirement: Script de lanzamiento usa los paths detectados para resolver el mapa
El script `scripts/run.py` SHALL usar el `MAPS_DIR` determinado por SO al invocar `sc2.main.run_game` con el mapa configurado.

#### Scenario: Mapa encontrado en el path correcto
- **WHEN** el mapa `AcropolisLE` existe en `MAPS_DIR`
- **THEN** `run_game` SHALL iniciar con ese mapa sin errores de path

#### Scenario: Mapa no encontrado
- **WHEN** el mapa `AcropolisLE` no existe en `MAPS_DIR`
- **THEN** el script SHALL lanzar `RuntimeError` con un mensaje que indique el path esperado y sugiera ejecutar el script de setup de mapas correspondiente
