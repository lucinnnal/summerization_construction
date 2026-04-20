#!/usr/bin/env bash
# Run the summarization script against a running vLLM server.
# Environment variables:
#   VLLM_HOST  : vLLM server base URL (default: http://localhost:8000/v1)
#   MODEL_NAME : model name passed to the API (default: LGAI-EXAONE/EXAONE-4.0-32B)
#   INPUT_FILE : input JSONL path  (default: data/filtered_combined_data.jsonl)
#   OUTPUT_FILE: output JSONL path (default: data/summarized_data.jsonl)
#   TEMPERATURE: sampling temperature (default: 0.3)
#   MAX_TOKENS : max tokens per response (default: 4096)

set -euo pipefail

VLLM_HOST="${VLLM_HOST:-http://localhost:8000/v1}"
MODEL_NAME="${MODEL_NAME:-LGAI-EXAONE/EXAONE-4.0-32B}"
INPUT_FILE="${INPUT_FILE:-data/filtered_combined_data.jsonl}"
OUTPUT_FILE="${OUTPUT_FILE:-data/summarized_data.jsonl}"
TEMPERATURE="${TEMPERATURE:-0.3}"
MAX_TOKENS="${MAX_TOKENS:-4096}"

echo "========================================"
echo "  Running summarization"
echo "  Host    : ${VLLM_HOST}"
echo "  Model   : ${MODEL_NAME}"
echo "  Input   : ${INPUT_FILE}"
echo "  Output  : ${OUTPUT_FILE}"
echo "========================================"

python summarize_with_exaone.py \
    --input  "${INPUT_FILE}" \
    --output "${OUTPUT_FILE}" \
    --host   "${VLLM_HOST}" \
    --model  "${MODEL_NAME}" \
    --temperature "${TEMPERATURE}" \
    --max-tokens  "${MAX_TOKENS}"
