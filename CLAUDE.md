# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

EXAONE-4.0-32B 모델을 vLLM으로 서빙하여 유튜브 영상의 트랜스크립트와 필터링된 댓글을 바탕으로 요약 데이터셋을 생성하는 파이프라인입니다.

## 실행 명령어

### Docker (권장)
```bash
docker build -t summarize-exaone .

# GPU 1장
docker run --gpus all --rm \
  -v /path/to/data:/app/data \
  summarize-exaone

# GPU 2장 이상
docker run --gpus all --rm \
  -v /path/to/data:/app/data \
  -e TENSOR_PARALLEL_SIZE=2 \
  summarize-exaone
```

### 로컬 (분리 실행)
```bash
pip install -r requirements.txt

# 터미널 1
bash scripts/start_vllm_server.sh

# 터미널 2 (서버 준비 후)
bash scripts/run_summarize.sh
```

### 직접 실행
```bash
python summarize_with_exaone.py \
  --input data/filtered_combined_data.jsonl \
  --output data/summarized_data.jsonl \
  --host http://localhost:8000/v1
```

## 아키텍처

**실행 흐름 (Docker):** `entrypoint.sh` → vLLM 서버 기동 → 헬스체크(`/health`) 폴링(최대 300초) → `run_summarize.sh` → `summarize_with_exaone.py` → vLLM 종료

**요약 스크립트 (`summarize_with_exaone.py`):**
- OpenAI 호환 클라이언트로 vLLM에 연결 (`api_key="EMPTY"` — 로컬 전용)
- 이미 처리된 `video_id`를 출력 파일에서 읽어 자동 스킵 (재시작 안전)
- 실패 시 지수 백오프로 3회 재시도

**입력 JSONL 필드:** `video_id`, `video_url`, `title`, `channel_name`, `transcript[]`, `general_comments[]`, `timestamp_comments[]`

**출력 JSONL 필드:** `video_id`, `video_url`, `title`, `channel_name`, `summary` (1.비디오요약 / 2.시청자반응 / 3.하이라이트 구조)

## 주의사항

- `summarize_with_exaone.py` line 162에 `breakpoint()` 디버깅 코드가 있음 — 프로덕션 실행 전 반드시 제거
- `data/` 디렉토리는 Docker VOLUME으로 런타임에 마운트하므로 이미지에 포함되지 않음
- vLLM은 `--trust-remote-code` 플래그로 실행됨 (EXAONE 모델 요구사항)
