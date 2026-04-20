# summarize_project

EXAONE-4.0-32B 모델을 vLLM으로 서빙하여 유튜브 영상의 트랜스크립트와 필터링된 댓글을 바탕으로 요약 데이터셋을 생성하는 프로젝트입니다.

---

## 프로젝트 구조

```
summarize_project/
├── Dockerfile                   # CUDA 12.1 기반 컨테이너 이미지
├── requirements.txt             # Python 의존성 (vllm, openai)
├── summarize_with_exaone.py     # 요약 생성 메인 스크립트
├── scripts/
│   ├── entrypoint.sh            # 컨테이너 진입점 (vLLM 시작 → 요약 실행 → 종료)
│   ├── start_vllm_server.sh     # vLLM OpenAI 서버 단독 실행
│   └── run_summarize.sh         # 요약 스크립트 단독 실행
└── data/                        # 입출력 데이터 디렉토리 (런타임에 마운트)
    ├── filtered_combined_data.jsonl   # 입력 파일 (직접 복사해서 사용)
    └── summarized_data.jsonl          # 출력 파일 (자동 생성)
```

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
# 1. 이미지 빌드
docker build -t summarize-exaone .

# 2. 실행 (GPU 1장)
docker run --gpus all --rm \
  -v /path/to/summarize_project/data:/app/data \
  summarize-exaone

# GPU 2장 이상인 경우
docker run --gpus all --rm \
  -v /path/to/summarize_project/data:/app/data \
  -e TENSOR_PARALLEL_SIZE=2 \
  summarize-exaone
```

컨테이너 실행 시 내부 동작 순서:
1. vLLM 서버 백그라운드 실행
2. 서버 준비 완료까지 헬스체크 대기 (최대 300초)
3. 요약 스크립트 실행
4. 완료 후 vLLM 프로세스 종료

### 로컬 (vLLM 서버와 요약 스크립트 분리 실행)

```bash
pip install -r requirements.txt

# 터미널 1: vLLM 서버 실행
bash scripts/start_vllm_server.sh

# 터미널 2: 요약 실행 (서버가 준비된 후)
bash scripts/run_summarize.sh
```

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `MODEL_NAME` | `LGAI-EXAONE/EXAONE-4.0-32B` | HuggingFace 모델 ID |
| `TENSOR_PARALLEL_SIZE` | `1` | 사용할 GPU 수 |
| `GPU_MEMORY_UTILIZATION` | `0.90` | GPU 메모리 사용 비율 |
| `MAX_MODEL_LEN` | `8192` | 최대 컨텍스트 길이 |
| `VLLM_PORT` | `8000` | vLLM 서버 포트 |
| `INPUT_FILE` | `data/filtered_combined_data.jsonl` | 입력 파일 경로 |
| `OUTPUT_FILE` | `data/summarized_data.jsonl` | 출력 파일 경로 |
| `TEMPERATURE` | `0.3` | 샘플링 온도 |
| `MAX_TOKENS` | `4096` | 요약 최대 토큰 수 |
| `MAX_WAIT_SEC` | `300` | vLLM 서버 대기 최대 시간(초) |

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
