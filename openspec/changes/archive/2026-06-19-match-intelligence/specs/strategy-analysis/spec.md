## ADDED Requirements

### Requirement: Analysis script aggregates match reports
The system SHALL include a `scripts/analyze.sh` bash script that aggregates JSON reports from the `reports/` directory, computes cross-match metrics, and generates a structured prompt for LLM analysis.

#### Scenario: Script aggregates multiple matches
- **WHEN** `scripts/analyze.sh` is run with `--matches 5`
- **THEN** it SHALL read the 5 most recent `reports/*/report.json` files and compute aggregate metrics

#### Scenario: Aggregate metrics computed
- **WHEN** multiple match reports are aggregated
- **THEN** the script SHALL compute: average supply_blocks, average unspent_minerals, average peak_workers, win rate, and expansion_timing average

#### Scenario: Missing jq produces clear error
- **WHEN** `jq` is not installed on the system
- **THEN** the script SHALL print a clear error message with installation instructions for macOS (`brew install jq`) and exit with code 1

#### Scenario: Dry run mode shows prompt without API call
- **WHEN** `scripts/analyze.sh --dry-run` is executed
- **THEN** the constructed LLM prompt SHALL be printed to stdout and no API call SHALL be made

### Requirement: Analysis script retrieves relevant code via CodeGraph
The system SHALL use the `codegraph` CLI to retrieve source code snippets for functions responsible for detected problem areas, and include those snippets in the LLM prompt.

#### Scenario: Code snippet retrieved for supply block problem
- **WHEN** aggregate metrics show `avg_supply_blocks > 0`
- **THEN** the script SHALL run `codegraph node src/bot/core.py:manage_pylons` and include the output in the prompt

#### Scenario: Code snippet retrieved for worker stall problem
- **WHEN** aggregate metrics show `avg_peak_workers < 70`
- **THEN** the script SHALL run `codegraph node src/bot/core.py:manage_probes` and include the output in the prompt

#### Scenario: Graceful handling of missing codegraph
- **WHEN** `codegraph` CLI is not available
- **THEN** the script SHALL print a warning that code snippets are unavailable and continue without them

### Requirement: Analysis script calls LLM API with configurable model
The system SHALL read `SC2AI_LLM_*` environment variables from `.env` and use them to construct and send an API request to the LLM provider. The model, base URL, and parameters SHALL be configurable through these variables.

#### Scenario: API call succeeds with configured model
- **WHEN** all `SC2AI_LLM_*` variables are set and the API is reachable
- **THEN** a JSON payload SHALL be sent via `curl` and the response SHALL be saved

#### Scenario: Missing API key produces clear error
- **WHEN** `SC2AI_LLM_API_KEY` is not set
- **THEN** the script SHALL print "SC2AI_LLM_API_KEY is not set. Copy .env.example to .env and fill in your key." and exit

#### Scenario: Model override via CLI argument
- **WHEN** `scripts/analyze.sh --model minimax-m2.7` is executed
- **THEN** the API request SHALL use `minimax-m2.7` instead of the `.env` default

#### Scenario: Analysis output saved to reports/analysis/
- **WHEN** the LLM response is received
- **THEN** it SHALL be saved as `reports/analysis/analysis_YYYYMMDD_HHMMSS.md` with a timestamped filename

### Requirement: .env.example is committed as documented template
The system SHALL include a committed `.env.example` file documenting all `SC2AI_LLM_*` environment variables with their defaults and usage descriptions.

#### Scenario: .env.example exists with all variables
- **WHEN** inspecting `.env.example`
- **THEN** all `SC2AI_LLM_*` variables SHALL be present with placeholder values and descriptive comments

#### Scenario: .env is gitignored
- **WHEN** running `git status`
- **THEN** `.env` SHALL NOT appear as untracked (it is in `.gitignore`)
