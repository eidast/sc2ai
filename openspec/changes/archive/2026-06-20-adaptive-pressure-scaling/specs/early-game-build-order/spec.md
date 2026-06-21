## ADDED Requirements

### Requirement: Early game fast expand when pressure is low
The system SHALL add a fast-expand phase to `manage_early_game()` after the Cybernetics Core phase. When pressure level is NONE or LOW and `expansion_count < 2`, the bot SHALL attempt to build a Nexus at the natural expansion location. If pressure is MEDIUM or HIGH, or the bot already has 2+ Nexuses, this phase SHALL be skipped.

#### Scenario: Fast expand when pressure is NONE
- **WHEN** early game phase is 2.5 (after CyberCore), pressure is NONE, expansion_count < 2, and can afford Nexus
- **THEN** `manage_early_game` SHALL build a Nexus

#### Scenario: Fast expand skipped under pressure
- **WHEN** early game phase is 2.5, pressure is MEDIUM, expansion_count < 2
- **THEN** `manage_early_game` SHALL skip the Nexus and proceed to phase 3 (Warpgate Research)

#### Scenario: Fast expand skipped when already expanded
- **WHEN** early game phase is 2.5, pressure is NONE, expansion_count >= 2
- **THEN** `manage_early_game` SHALL skip the Nexus and proceed to phase 3
