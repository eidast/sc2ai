## ADDED Requirements

### Requirement: CLI acepta configuracion de oponente
El script `scripts/run.py` SHALL aceptar los flags `--difficulty`, `--opponent-race` y `--opponents` para configurar los oponentes controlados por la IA. Los valores por defecto SHALL ser `Medium`, `Terran`, y `1` respectivamente, manteniendo compatibilidad con el comportamiento actual.

#### Scenario: Dificultad configurada por el usuario
- **WHEN** el script se ejecuta con `--difficulty Hard`
- **THEN** el oponente SHALL ser creado con `Difficulty.Hard`

#### Scenario: Raza del oponente configurada por el usuario
- **WHEN** el script se ejecuta con `--opponent-race Zerg`
- **THEN** el oponente SHALL ser creado con `Race.Zerg`

#### Scenario: Numero de oponentes configurado por el usuario
- **WHEN** el script se ejecuta con `--opponents 2`
- **THEN** dos oponentes SHALL ser creados, ambos con la misma dificultad y raza

#### Scenario: Valores por defecto cuando no se especifican flags
- **WHEN** el script se ejecuta sin `--difficulty`, `--opponent-race`, ni `--opponents`
- **THEN** el oponente SHALL ser `Computer(Race.Terran, Difficulty.Medium)`, exactamente un oponente

### Requirement: Validacion de valores de flags de oponente
El script SHALL rechazar valores invalidos para los flags de configuracion de oponente con un mensaje de error claro.

#### Scenario: Dificultad invalida rechazada
- **WHEN** el script se ejecuta con `--difficulty Impossible`
- **THEN** argparse SHALL mostrar un error indicando que el valor no es valido y listando las opciones permitidas

#### Scenario: Raza invalida rechazada
- **WHEN** el script se ejecuta con `--opponent-race XelNaga`
- **THEN** argparse SHALL mostrar un error indicando que el valor no es valido y listando las opciones permitidas

#### Scenario: Dificultades con cheat no permitidas
- **WHEN** se listan las opciones validas de `--difficulty`
- **THEN** las dificultades `CheatVision`, `CheatMoney`, y `CheatInsane` NO SHALL aparecer en la lista

#### Scenario: Numero de oponentes fuera de rango rechazado
- **WHEN** el script se ejecuta con `--opponents 0` o `--opponents 5`
- **THEN** argparse SHALL mostrar un error indicando que el valor debe estar entre 1 y 4

### Requirement: Bot recibe configuracion de oponente para el reporte
El bot `MyBot` SHALL recibir los valores de configuracion de oponente (`opponent_difficulty`, `opponent_race`, `opponent_count`) en su constructor y usarlos para generar `bot_info` en `on_end()`, reemplazando los strings hardcodeados actuales.

#### Scenario: Reporte refleja dificultad real
- **WHEN** la partida se ejecuta con `--difficulty VeryHard`
- **THEN** el archivo `report.json` SHALL contener `"opponent_difficulty": "VeryHard"`

#### Scenario: Reporte refleja raza real
- **WHEN** la partida se ejecuta con `--opponent-race Zerg`
- **THEN** el archivo `report.json` SHALL contener `"opponent_race": "Zerg"`

#### Scenario: Retrocompatibilidad con defaults
- **WHEN** la partida se ejecuta sin flags de oponente
- **THEN** el archivo `report.json` SHALL contener `"opponent_difficulty": "Medium"` y `"opponent_race": "Terran"`
