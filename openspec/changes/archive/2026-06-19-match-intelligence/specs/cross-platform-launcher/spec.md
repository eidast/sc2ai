## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Script de lanzamiento acepta --realtime
El script `scripts/run.py` SHALL aceptar un flag `--realtime` que, cuando está presente, configura `run_game(realtime=True)` para ejecutar la partida a velocidad normal con renderizado habilitado.

#### Scenario: Partida en tiempo real
- **WHEN** el script se ejecuta con `--realtime`
- **THEN** `run_game` SHALL ser invocado con `realtime=True`

#### Scenario: Partida acelerada por defecto
- **WHEN** el script se ejecuta sin `--realtime`
- **THEN** `run_game` SHALL ser invocado con `realtime=False`
