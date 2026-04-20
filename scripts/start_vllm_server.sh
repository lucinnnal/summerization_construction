#!/usr/bin/env bash
# Start vLLM OpenAI-compatible server for EXAONE-4.0-32B.
# Environment variables (override via -e in docker run or export in shell):
#   MODEL_NAME   : HuggingFace model ID  (default: LGAI-EXAONE/EXAONE-4.0-32B)
#   TENSOR_PARALLEL_SIZE : number of GPUs (default: 1)
#   GPU_MEMORY_UTILIZATION : fraction of VRAM to use (default: 0.90)
#   MAX_MODEL_LEN : max context length (default: 8192)
#   VLLM_PORT    : server port (default: 8000)

set -euo pipefail

MODEL_NAME="${MODEL_NAME:-LGAI-EXAONE/EXAONE-4.0-32B}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
VLLM_PORT="${VLLM_PORT:-8000}"

echo "========================================"
echo "  Starting vLLM server"
echo "  Model   : ${MODEL_NAME}"
echo "  TP size : ${TENSOR_PARALLEL_SIZE}"
echo "  Port    : ${VLLM_PORT}"
echo "========================================"

exec python -m vllm.entrypoints.openai.api_server \
    --model "${MODEL_NAME}" \
    --tensor-parallel-size "${TENSOR_PARALLEL_SIZE}" \
    --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}" \
    --max-model-len "${MAX_MODEL_LEN}" \
    --dtype bfloat16 \
    --trust-remote-code \
    --port "${VLLM_PORT}" \
    --host 0.0.0.0
