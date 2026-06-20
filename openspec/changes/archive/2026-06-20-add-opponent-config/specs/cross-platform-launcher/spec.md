## ADDED Requirements

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
