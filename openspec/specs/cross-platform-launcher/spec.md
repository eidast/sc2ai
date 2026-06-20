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
El script `scripts/run.py` SHALL usar el `MAPS_DIR` determinado por SO al invocar `sc2.main.run_game` con el mapa configurado. El mapa SHALL ser configurable mediante el argumento CLI `--map`, aceptando un nombre de mapa específico o el valor `random` para selección aleatoria.

#### Scenario: Mapa encontrado en el path correcto
- **WHEN** el mapa especificado (por `--map` o default `AcropolisLE`) existe en `MAPS_DIR`
- **THEN** `run_game` SHALL iniciar con ese mapa sin errores de path

#### Scenario: Mapa no encontrado
- **WHEN** el mapa especificado no existe en `MAPS_DIR`
- **THEN** el script SHALL lanzar `RuntimeError` con un mensaje que indique el path esperado y sugiera ejecutar el script de setup de mapas correspondiente

#### Scenario: Mapa aleatorio seleccionado
- **WHEN** el argumento `--map random` es usado
- **THEN** el script SHALL seleccionar aleatoriamente un mapa de los disponibles en `MAPS_DIR` y usarlo

#### Scenario: Mapa por defecto es AcropolisLE
- **WHEN** el script se ejecuta sin el argumento `--map`
- **THEN** el mapa `AcropolisLE` SHALL ser usado como default

### Requirement: Script de lanzamiento acepta --realtime
El script `scripts/run.py` SHALL aceptar un flag `--realtime` que, cuando está presente, configura `run_game(realtime=True)` para ejecutar la partida a velocidad normal con renderizado habilitado.

#### Scenario: Partida en tiempo real
- **WHEN** el script se ejecuta con `--realtime`
- **THEN** `run_game` SHALL ser invocado con `realtime=True`

#### Scenario: Partida acelerada por defecto
- **WHEN** el script se ejecuta sin `--realtime`
- **THEN** `run_game` SHALL ser invocado con `realtime=False`

### Requirement: Script de lanzamiento acepta --difficulty
El script `scripts/run.py` SHALL aceptar un flag `--difficulty` que, cuando esta presente, configura la dificultad del oponente IA. Los valores aceptados SHALL ser `VeryEasy`, `Easy`, `Medium`, `MediumHard`, `Hard`, `Harder`, `VeryHard`. El valor por defecto SHALL ser `Medium`.

#### Scenario: Dificultad configurada via CLI
- **WHEN** el script se ejecuta con `--difficulty Hard`
- **THEN** `run_game` SHALL ser invocado con `Computer` usando `Difficulty.Hard`

#### Scenario: Dificultad por defecto
- **WHEN** el script se ejecuta sin `--difficulty`
- **THEN** `run_game` SHALL ser invocado con `Computer` usando `Difficulty.Medium`

### Requirement: Script de lanzamiento acepta --opponent-race
El script `scripts/run.py` SHALL aceptar un flag `--opponent-race` que, cuando esta presente, configura la raza del oponente IA. Los valores aceptados SHALL ser `Terran`, `Zerg`, `Protoss`, `Random`. El valor por defecto SHALL ser `Terran`.

#### Scenario: Raza configurada via CLI
- **WHEN** el script se ejecuta con `--opponent-race Zerg`
- **THEN** `run_game` SHALL ser invocado con `Computer` usando `Race.Zerg`

#### Scenario: Raza por defecto
- **WHEN** el script se ejecuta sin `--opponent-race`
- **THEN** `run_game` SHALL ser invocado con `Computer` usando `Race.Terran`

### Requirement: Script de lanzamiento acepta --opponents
El script `scripts/run.py` SHALL aceptar un flag `--opponents` que, cuando esta presente, configura el numero de oponentes IA. El valor SHALL ser un entero entre 1 y 4 inclusive. El valor por defecto SHALL ser `1`. Todos los oponentes compartiran la misma dificultad y raza.

#### Scenario: Multiples oponentes configurados via CLI
- **WHEN** el script se ejecuta con `--opponents 2 --difficulty Hard`
- **THEN** `run_game` SHALL ser invocado con dos `Computer`, ambos con `Difficulty.Hard`

#### Scenario: Numero de oponentes por defecto
- **WHEN** el script se ejecuta sin `--opponents`
- **THEN** `run_game` SHALL ser invocado con exactamente un `Computer`
