## 1. OpenSpec documentation

- [x] 1.1 Create follow-up change artifacts for the five verification warnings

## 2. Launch map handling

- [x] 2.1 Add failing tests for configured map resolution and clear missing-map errors
- [x] 2.2 Implement map resolution helper in `scripts/run.py`

## 3. Observation logging

- [x] 3.1 Add failing tests for configurable `MyBot(log_interval=44)` behavior
- [x] 3.2 Add failing tests for feature dictionary log output
- [x] 3.3 Implement configurable log interval and dictionary logging

## 4. Project documentation

- [x] 4.1 Add failing test for Spanish-first then English-second README ordering
- [x] 4.2 Restructure `README.md` into clear Spanish and English sections

## 5. Feature extraction coverage

- [x] 5.1 Add test for required `extract_features()` keys and empty/default-friendly values

## 6. Verification

- [x] 6.1 Run `uv run pytest`
- [x] 6.2 Run `openspec status --change "fix-foundation-verification-warnings" --json`
