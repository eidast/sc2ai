## MODIFIED Requirements

### Requirement: Bilingual README
The project SHALL include a README.md with content in both Spanish and English. Spanish content SHALL appear first, followed by English content, and each language SHALL have a clear section header.

#### Scenario: README is accessible and bilingual
- **WHEN** viewing the repository on GitHub
- **THEN** the README SHALL display Spanish content followed by English content, with clear language section headers

## ADDED Requirements

### Requirement: Foundation behavior has automated coverage
The project SHALL include pytest coverage for foundation behavior that can be validated without launching a full StarCraft II match.

#### Scenario: Local verification runs successfully
- **WHEN** running `uv run pytest`
- **THEN** tests for map error handling, logging interval configuration, feature dictionary logging, feature extraction shape, and README language ordering SHALL pass
