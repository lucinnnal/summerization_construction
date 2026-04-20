# ── Base: PyTorch 2.3 + CUDA 12.1 (vLLM-compatible) ─────────────────────────
FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-devel

WORKDIR /app

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        git \
        wget \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application files ─────────────────────────────────────────────────────────
COPY summarize_with_exaone.py .
COPY scripts/ scripts/
RUN chmod +x scripts/entrypoint.sh scripts/start_vllm_server.sh scripts/run_summarize.sh

# ── Data volume (mount input/output JSONL files here at runtime) ──────────────
VOLUME ["/app/data"]

# ── Default environment variables (override with -e in docker run) ────────────
ENV MODEL_NAME="LGAI-EXAONE/EXAONE-4.0-32B" \
    TENSOR_PARALLEL_SIZE="1" \
    GPU_MEMORY_UTILIZATION="0.90" \
    MAX_MODEL_LEN="8192" \
    VLLM_PORT="8000" \
    INPUT_FILE="data/filtered_combined_data.jsonl" \
    OUTPUT_FILE="data/summarized_data.jsonl" \
    TEMPERATURE="0.3" \
    MAX_TOKENS="4096" \
    MAX_WAIT_SEC="300"

EXPOSE 8000

ENTRYPOINT ["bash", "/app/scripts/entrypoint.sh"]
