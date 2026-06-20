## ADDED Requirements

### Requirement: Script batch descarga map packs de Blizzard en Windows 11
El sistema SHALL incluir un script `scripts/setup_maps.bat` que descarga y extrae los map packs oficiales de Blizzard en Windows 11 sin requerir la instalación de herramientas externas adicionales.

#### Scenario: Descarga exitosa de map packs
- **WHEN** el usuario ejecuta `scripts\setup_maps.bat` en Windows 11 con conexión a internet
- **THEN** el script SHALL descargar `Ladder2019Season3.zip` y `Melee.zip` desde los servidores oficiales de Blizzard usando `curl`

#### Scenario: Extracción de zips con contraseña
- **WHEN** los archivos zip se han descargado
- **THEN** el script SHALL extraerlos al directorio `C:\Program Files (x86)\StarCraft II\Maps\` usando PowerShell con `-ExecutionPolicy Bypass` para manejar la contraseña `iagreetotheeula` sin requerir intervención del usuario

#### Scenario: Directorio de mapas no existe
- **WHEN** el directorio `C:\Program Files (x86)\StarCraft II\Maps\` no existe
- **THEN** el script SHALL crearlo antes de la descarga

#### Scenario: Limpieza de archivos temporales
- **WHEN** la extracción se completa (con éxito o error)
- **THEN** el script SHALL eliminar los archivos zip temporales del directorio `%TEMP%`

### Requirement: Script batch muestra progreso y resultado
El script `scripts/setup_maps.bat` SHALL mostrar mensajes de progreso en la terminal para que el usuario sepa qué está ocurriendo.

#### Scenario: Inicio del script
- **WHEN** el script inicia
- **THEN** SHALL mostrar un mensaje con el título "SC2AI Map Setup (Windows)" y el directorio destino

#### Scenario: Finalización exitosa
- **WHEN** todos los mapas se han descargado y extraído correctamente
- **THEN** SHALL mostrar un mensaje de éxito y un comando de verificación
