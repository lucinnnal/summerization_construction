# summarize_project

vLLM으로 EXAONE 모델을 서빙하여 유튜브 영상의 트랜스크립트와 필터링된 댓글을 바탕으로 요약 데이터셋을 생성하는 프로젝트입니다.

---

## 프로젝트 구조

```
summarize_project/
├── Dockerfile                        # CUDA 12.6, MODEL_FAMILY ARG로 모델별 분기
├── requirements.txt                  # 공통 Python 의존성 (openai, pyyaml)
├── summarize_with_exaone.py          # 요약 생성 메인 스크립트
├── configs/
│   ├── exaone40.yaml                 # EXAONE 4.0 전용 vLLM 인자 + generation config
│   └── exaone45.yaml                 # EXAONE 4.5 전용 vLLM 인자 + generation config
├── scripts/
│   ├── entrypoint.sh                 # 컨테이너 진입점 (vLLM 시작 → 요약 실행 → 종료)
│   ├── start_vllm_server.sh          # vLLM 서버 단독 실행 (launch_vllm.py 호출)
│   ├── launch_vllm.py                # YAML config 읽어 vLLM 커맨드 빌드 및 실행
│   └── run_summarize.sh              # 요약 스크립트 단독 실행
└── data/                             # 입출력 데이터 디렉토리 (런타임에 마운트)
    ├── filtered_combined_data.jsonl  # 입력 파일 (직접 복사해서 사용)
    └── summarized_data.jsonl         # 출력 파일 (자동 생성)
```

---

## 지원 모델

| MODEL_FAMILY | 모델 ID | vLLM 특이사항 |
|---|---|---|
| `exaone40` | `LGAI-EXAONE/EXAONE-4.0-32B` | `--reasoning-parser deepseek_r1` |
| `exaone45` | `LGAI-EXAONE/EXAONE-4.5-33B` | `--reasoning-parser qwen3`, forked vllm/transformers 사용 |

### 모델별 설정 파일 구조

`configs/{model_family}.yaml` 에 vLLM 서버 인자와 generation config가 함께 관리됩니다.

```yaml
# configs/exaone40.yaml 예시
model_name: "LGAI-EXAONE/EXAONE-4.0-32B"

vllm:
  reasoning_parser: "deepseek_r1"

generation:
  temperature: 0.6
  top_p: 0.95
  max_tokens: 4096
  chat_template_kwargs:
    enable_thinking: true
    skip_think: false
```

새 모델 추가 시 `configs/` 에 YAML 파일을 추가하고, Dockerfile의 vllm 설치 분기를 업데이트하면 됩니다.

---

## 입력 데이터 준비

`data/` 폴더에 입력 파일을 복사합니다.

```bash
cp /path/to/filtered_combined_data.jsonl \
   /path/to/summarize_project/data/
```

입력 파일(`filtered_combined_data.jsonl`)의 각 레코드는 다음 필드를 포함해야 합니다:

| 필드 | 설명 |
|------|------|
| `video_id` | 유튜브 영상 ID |
| `video_url` | 유튜브 영상 URL |
| `title` | 영상 제목 |
| `channel_name` | 채널명 |
| `transcript` | 자막 세그먼트 리스트 |
| `general_comments` | 필터링된 일반 댓글 리스트 |
| `timestamp_comments` | 필터링된 타임스탬프 댓글 리스트 |

---

## 실행 방법

### Docker (권장)

```bash
# EXAONE 4.0 이미지 빌드
docker build --build-arg MODEL_FAMILY=exaone40 -t summarize:exaone40 .

# EXAONE 4.5 이미지 빌드 (forked vllm/transformers 포함)
docker build --build-arg MODEL_FAMILY=exaone45 -t summarize:exaone45 .
```

```bash
# EXAONE 4.0 실행 (GPU 1장)
docker run --gpus all --rm \
  -v /path/to/summarize_project/data:/app/data \
  summarize:exaone40

# EXAONE 4.5 실행 (GPU 1장)
docker run --gpus all --rm \
  -v /path/to/summarize_project/data:/app/data \
  summarize:exaone45

# GPU 여러 장 사용 시
docker run --gpus all --rm \
  -v /path/to/summarize_project/data:/app/data \
  -e TENSOR_PARALLEL_SIZE=2 \
  summarize:exaone40
```

컨테이너 실행 시 내부 동작 순서:
1. vLLM 서버 백그라운드 실행 (모델별 vllm 인자 자동 적용)
2. 서버 준비 완료까지 헬스체크 대기 (최대 300초)
3. 요약 스크립트 실행 (모델별 generation config 자동 적용)
4. 완료 후 vLLM 프로세스 종료

### 로컬 (vLLM 서버와 요약 스크립트 분리 실행)

```bash
pip install -r requirements.txt

# EXAONE 4.0 vllm 설치
pip install vllm==0.10.0

# EXAONE 4.5 vllm 설치 (forked)
pip install git+https://github.com/lkm2835/vllm.git@add-exaone4_5
pip install git+https://github.com/nuxlear/transformers.git@add-exaone4_5

# 터미널 1: vLLM 서버 실행
export MODEL_FAMILY=exaone40  # 또는 exaone45
bash scripts/start_vllm_server.sh

# 터미널 2: 요약 실행 (서버가 준비된 후)
export MODEL_FAMILY=exaone40
bash scripts/run_summarize.sh
```

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `MODEL_FAMILY` | `exaone40` | 사용할 모델 config 키 |
| `MODEL_NAME` | YAML의 `model_name` | vLLM에 로드할 HuggingFace 모델 ID (override) |
| `TENSOR_PARALLEL_SIZE` | `1` | 사용할 GPU 수 |
| `GPU_MEMORY_UTILIZATION` | `0.90` | GPU 메모리 사용 비율 |
| `MAX_MODEL_LEN` | YAML의 `vllm.max_model_len` | 최대 컨텍스트 길이 (override) |
| `VLLM_PORT` | `8000` | vLLM 서버 포트 |
| `INPUT_FILE` | `data/filtered_combined_data.jsonl` | 입력 파일 경로 |
| `OUTPUT_FILE` | `data/summarized_data.jsonl` | 출력 파일 경로 |
| `TEMPERATURE` | YAML의 `generation.temperature` | 샘플링 온도 (override) |
| `TOP_P` | YAML의 `generation.top_p` | top-p 값 (override) |
| `MAX_TOKENS` | YAML의 `generation.max_tokens` | 요약 최대 토큰 수 (override) |
| `MAX_WAIT_SEC` | `300` | vLLM 서버 대기 최대 시간(초) |

`MODEL_NAME`, `MAX_MODEL_LEN`, `TEMPERATURE`, `TOP_P`, `MAX_TOKENS`는 YAML config 값을 기본으로 하되, 환경 변수로 개별 override 가능합니다.

---

## 출력

### 경로

```
data/summarized_data.jsonl
```

### 포맷

JSONL 형식으로 영상 1개당 1줄씩 저장됩니다.

```json
{
  "video_id": "abc123",
  "video_url": "https://www.youtube.com/watch?v=abc123",
  "title": "영상 제목",
  "channel_name": "채널명",
  "summary": "1. 비디오 요약\n...\n2. 시청자 반응 요약\n...\n3. 주요 하이라이트\n..."
}
```

`summary` 필드는 다음 세 섹션으로 구성됩니다:

| 섹션 | 내용 |
|------|------|
| 1. 비디오 요약 | 트랜스크립트 기반 5~6문장 요약 |
| 2. 시청자 반응 요약 | 일반 댓글 분석 — 주된 여론, 공감 포인트 |
| 3. 주요 하이라이트 | 타임스탬프 댓글 기반 장면별 하이라이트 |

### 재시작 안전성

이미 처리된 `video_id`는 자동으로 스킵되므로 중간에 중단되어도 이어서 실행할 수 있습니다.
