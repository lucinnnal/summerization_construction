---
name: analyze-data
description: 입력 데이터(filtered_combined_data.jsonl)의 댓글 수 분포를 분석하고 시각화합니다. general_comments/timestamp_comments 분포, 평균, 히스토그램 차트 생성.
when_to_use: |
  아래 표현이 나오면 이 스킬을 사용하세요:
  - "데이터 분석", "댓글 분포", "댓글 수 분포"
  - "히스토그램", "시각화", "차트 만들어줘"
  - "general_comments / timestamp_comments 통계"
  - "평균 댓글 수", "최솟값/최댓값"
  사용하지 않을 때: 진행 상황 확인 → summarize-progress 사용
---

아래 명령어를 실행하고 결과를 한국어로 출력하세요.

```bash
python3 .claude/skills/analyze-data/analyze.py
```

실행 후 통계 수치를 그대로 출력하고, 차트 저장 경로(`data/comment_stats.png`)를 안내하세요.
