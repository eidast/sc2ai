#!/usr/bin/env bash
set -euo pipefail

# SC2AI Strategy Analysis Pipeline
# Aggregates match reports, retrieves relevant code via CodeGraph,
# and calls the LLM API for strategy improvement suggestions.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/reports"
ENV_FILE="$PROJECT_ROOT/.env"

N_MATCHES=10
MODEL=""
DRY_RUN=false
OUTPUT_DIR="$REPORTS_DIR/analysis"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Aggregate match reports and generate LLM analysis for strategy improvement.

Options:
  --matches N    Number of most recent matches to analyze (default: 10)
  --model MODEL  Override the model from .env (e.g., minimax-m2.7)
  --dry-run      Build the prompt and print it without calling the API
  --help         Show this message

Environment (.env):
  SC2AI_LLM_API_KEY          OpenCode Go/Zen API key (required)
  SC2AI_LLM_MODEL            Model ID (default: opencode-go/deepseek-v4-pro)
  SC2AI_LLM_BASE_URL         API endpoint (default: https://opencode.ai/zen/v1)
  SC2AI_LLM_MAX_TOKENS       Max output tokens (default: 32768)
  SC2AI_LLM_REASONING_EFFORT Reasoning effort: none|minimal|low|medium|high|xhigh (default: max)
  SC2AI_LLM_TEMPERATURE      Sampling temperature (default: 0.7)
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --matches) N_MATCHES="$2"; shift 2 ;;
        --model)   MODEL="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help)    usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if ! command -v jq &>/dev/null; then
    echo "Error: 'jq' is required but not installed."
    echo "Install it with: brew install jq  (macOS)"
    echo "                  apt-get install jq  (Linux/WSL)"
    exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

API_KEY="${SC2AI_LLM_API_KEY:-}"
MODEL="${MODEL:-${SC2AI_LLM_MODEL:-opencode-go/deepseek-v4-pro}}"
BASE_URL="${SC2AI_LLM_BASE_URL:-https://opencode.ai/zen/v1}"
MAX_TOKENS="${SC2AI_LLM_MAX_TOKENS:-32768}"
REASONING="${SC2AI_LLM_REASONING_EFFORT:-max}"
TEMPERATURE="${SC2AI_LLM_TEMPERATURE:-0.7}"

if [[ -z "$API_KEY" ]]; then
    echo "Error: SC2AI_LLM_API_KEY is not set."
    echo "Copy .env.example to .env and fill in your key, or set the environment variable."
    exit 1
fi

if [[ ! -d "$REPORTS_DIR" ]]; then
    echo "No reports/ directory found. Run some matches first."
    exit 1
fi

echo "=== SC2AI Strategy Analysis ==="
echo "Matches to analyze: $N_MATCHES"
echo "Model: $MODEL"
echo ""

echo "[1/3] Aggregating match reports..."

REPORT_FILES=$(find "$REPORTS_DIR" -name report.json -not -path "*/analysis/*" | sort -r | head -n "$N_MATCHES")
MATCH_COUNT=$(echo "$REPORT_FILES" | grep -c . || true)

if [[ "$MATCH_COUNT" -eq 0 ]]; then
    echo "No match reports found in $REPORTS_DIR. Run some matches first."
    exit 1
fi

echo "Found $MATCH_COUNT match report(s)."

AGGREGATE_JSON=$(jq -s '{
    match_count: length,
    results: group_by(.result) | map({result: .[0].result, count: length}),
    avg_duration: (map(.duration_seconds) | add / length),
    avg_max_supply: (map(.max_supply_reached) | add / length),
    avg_supply_blocks: (map(.metrics.supply_block_count) | add / length),
    avg_unspent_minerals: (map(.metrics.avg_unspent_minerals) | add / length),
    avg_unspent_vespene: (map(.metrics.avg_unspent_vespene) | add / length),
    avg_peak_workers: (map(.metrics.peak_workers) | add / length),
    worker_target: .[0].metrics.worker_target,
    maps: group_by(.map) | map({map: .[0].map, count: length}),
    summaries: map({id: .match_id, map: .map, result: .result, duration: .duration_seconds, supply: .max_supply_reached, blocks: .metrics.supply_block_count, workers: .metrics.peak_workers, unspent: .metrics.avg_unspent_minerals})
}' <<< "$REPORT_FILES")

win_count=$(echo "$AGGREGATE_JSON" | jq '[.results[] | select(.result == "victory") | .count] | add // 0')
winrate=$(echo "scale=0; $win_count * 100 / $MATCH_COUNT" | bc 2>/dev/null || echo "?")

echo ""
echo "--- Aggregate Metrics ---"
echo "Matches: $MATCH_COUNT"
echo "Win rate: ${winrate}%"
echo "Avg duration: $(echo "$AGGREGATE_JSON" | jq '.avg_duration | floor')s"
echo "Avg max supply: $(echo "$AGGREGATE_JSON" | jq '.avg_max_supply | floor')"
echo "Avg supply blocks: $(echo "$AGGREGATE_JSON" | jq '.avg_supply_blocks * 100 | round / 100')"
echo "Avg unspent minerals: $(echo "$AGGREGATE_JSON" | jq '.avg_unspent_minerals | floor')"
echo "Avg peak workers: $(echo "$AGGREGATE_JSON" | jq '.avg_peak_workers | floor') / $(echo "$AGGREGATE_JSON" | jq '.worker_target')"

echo ""
echo "[2/3] Retrieving relevant code via CodeGraph..."

CODE_SNIPPETS=""

if command -v codegraph &>/dev/null; then
    avg_blocks=$(echo "$AGGREGATE_JSON" | jq -r '.avg_supply_blocks')
    if (( $(echo "$avg_blocks > 0" | bc -l 2>/dev/null || echo 1) )); then
        echo "  → supply_block problem detected, fetching manage_pylons..."
        SNIPPET=$(codegraph node "manage_pylons" 2>/dev/null || true)
        if [[ -n "$SNIPPET" ]]; then
            CODE_SNIPPETS+=$'\n'"### manage_pylons() — src/bot/core.py"$'\n'"\`\`\`python"$'\n'"$SNIPPET"$'\n'"\`\`\`"$'\n'
        fi
    fi

    avg_workers=$(echo "$AGGREGATE_JSON" | jq -r '.avg_peak_workers')
    target=$(echo "$AGGREGATE_JSON" | jq -r '.worker_target')
    if (( $(echo "$avg_workers < $target" | bc -l 2>/dev/null || echo 0) )); then
        echo "  → worker peak below target, fetching manage_probes..."
        SNIPPET=$(codegraph node "manage_probes" 2>/dev/null || true)
        if [[ -n "$SNIPPET" ]]; then
            CODE_SNIPPETS+=$'\n'"### manage_probes() — src/bot/core.py"$'\n'"\`\`\`python"$'\n'"$SNIPPET"$'\n'"\`\`\`"$'\n'
        fi
    fi

    avg_unspent=$(echo "$AGGREGATE_JSON" | jq -r '.avg_unspent_minerals')
    if (( $(echo "$avg_unspent > 300" | bc -l 2>/dev/null || echo 0) )); then
        echo "  → unspent minerals high, fetching manage_army..."
        SNIPPET=$(codegraph node "manage_army" 2>/dev/null || true)
        if [[ -n "$SNIPPET" ]]; then
            CODE_SNIPPETS+=$'\n'"### manage_army() — src/bot/core.py"$'\n'"\`\`\`python"$'\n'"$SNIPPET"$'\n'"\`\`\`"$'\n'
        fi
    fi
else
    echo "  ⚠ codegraph not found — skipping code retrieval"
    echo "  Install codegraph for source-level analysis: https://opencode.ai/docs"
fi

echo ""
echo "[3/3] Building LLM prompt..."

SYSTEM_PROMPT="You are a StarCraft II strategy analyst. You analyze Protoss bot match data and suggest specific, actionable code improvements in python-sc2. You are pragmatic and data-driven. All responses in Spanish."

USER_PROMPT=$(cat <<PROMPT
# Análisis SC2AI — Últimas $MATCH_COUNT partidas

## Resumen
- Win rate: ${winrate}%
- Partidas analizadas: $MATCH_COUNT

## Métricas agregadas
\`\`\`json
$AGGREGATE_JSON
\`\`\`

## Código relevante
$CODE_SNIPPETS

## Instrucciones
Basándote en estas métricas, por favor:
1. Identificá los 3 problemas más críticos (usá métricas, no especulación)
2. Para cada problema, citá la métrica específica que lo evidencia
3. Sugerí cambios concretos al código del bot que resolverían cada problema
4. Priorizá por impacto: ¿qué cambio produciría la mayor mejora en win rate?

Respuesta en español, formato Markdown, directo y accionable.
PROMPT
)

if $DRY_RUN; then
    echo "=== DRY RUN — Prompt below (no API call) ==="
    echo ""
    echo "$USER_PROMPT"
    echo ""
    echo "=== End of prompt ==="
    exit 0
fi

echo "Calling $MODEL via $BASE_URL..."

mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="$OUTPUT_DIR/analysis_${TIMESTAMP}.md"

PAYLOAD=$(jq -n \
    --arg model "$MODEL" \
    --arg system "$SYSTEM_PROMPT" \
    --arg user "$USER_PROMPT" \
    --argjson max_tokens "$MAX_TOKENS" \
    --arg reason "$REASONING" \
    --argjson temp "$TEMPERATURE" \
    '{
        model: $model,
        messages: [
            {role: "system", content: $system},
            {role: "user", content: $user}
        ],
        max_tokens: $max_tokens,
        reasoning_effort: $reason,
        temperature: $temp
    }')

HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/sc2ai_response.json \
    -X POST "$BASE_URL/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

if [[ "$HTTP_CODE" -ge 200 && "$HTTP_CODE" -lt 300 ]]; then
    jq -r '.choices[0].message.content' /tmp/sc2ai_response.json > "$OUTPUT_FILE"
    echo ""
    echo "✓ Analysis saved to: $OUTPUT_FILE"
    echo ""
    echo "--- Preview (first 500 chars) ---"
    head -c 500 "$OUTPUT_FILE"
    echo ""
    echo "..."
else
    echo ""
    echo "✗ API error (HTTP $HTTP_CODE):"
    cat /tmp/sc2ai_response.json
    exit 1
fi
