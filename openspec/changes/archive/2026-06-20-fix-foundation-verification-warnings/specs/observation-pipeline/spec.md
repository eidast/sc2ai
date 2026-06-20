## MODIFIED Requirements

### Requirement: Features are logged every N steps
The system SHALL log extracted features at a configurable interval (default every 22 steps, approximately 1 second) using Python's `logging` module. The bot SHALL allow callers to override this interval during initialization.

#### Scenario: Features appear in log output
- **WHEN** the bot runs with logging enabled at INFO level
- **THEN** the extracted feature dictionary SHALL appear in the console/log output at the configured interval

#### Scenario: Logging interval is configurable
- **WHEN** the bot is initialized with `log_interval=44`
- **THEN** features SHALL be logged every 44 steps instead of the default 22
