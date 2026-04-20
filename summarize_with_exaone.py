#!/usr/bin/env python3
"""
Generate video summaries using EXAONE 4.0 32B via vLLM.
Input: filtered_combined_data.jsonl
Output: summarized_data.jsonl
"""

import json
import os
import sys
import argparse
import time
from typing import List, Dict, Any

try:
    from openai import OpenAI
except ImportError:
    print("Please install openai: pip install openai")
    sys.exit(1)


def build_transcript_text(transcript: List[Dict[str, Any]]) -> str:
    """Join transcript segments into a single string."""
    return " ".join(item.get("text", "").strip() for item in transcript if item.get("text", "").strip())


def build_comments_text(comments: List[Dict[str, Any]]) -> str:
    """Format comment list as numbered text block."""
    if not comments:
        return "(없음)"
    lines = []
    for i, c in enumerate(comments, 1):
        text = c.get("text", "").strip()
        if text:
            lines.append(f"{i}. {text}")
    return "\n".join(lines) if lines else "(없음)"


def build_prompt(transcript_text: str, general_text: str, timestamp_text: str) -> str:
    """Build the summary prompt."""
    return f"""
당신은 유튜브 비디오의 트랜스크립트(자막)와 시청자 댓글을 바탕으로 고품질 요약을 생성하는 AI 전문가입니다.
제공된 트랜스크립트와 시청자 댓글(타임스탬프 댓글 및 일반 댓글)을 바탕으로 비디오에 대한 전반적인 요약, 시청자 반응, 그리고 주요 하이라이트를 종합적으로 정리해주세요.
다음 구조를 따라 한국어로 답변을 작성해주세요:
1. 비디오 요약 : 이 영상이 어떤 내용을 다루고 있는지 5~6문장으로 요약하세요.
2. 시청자 반응 요약 : 일반 시청자 댓글들을 분석하여 시청자들이 어떤 점에 공감하거나 반응했는지, 주된 여론이나 재미있는 포인트는 무엇인지 정리하세요.
3. 주요 하이라이트 : 타임스탬프 댓글을 기반으로 중요한 부분들을 정리하세요.

[중요]
*반드시 댓글에 기반하여 정확한 내용만 작성해야 합니다. 추측이나 과장된 표현은 피해주세요.*

[입력 데이터]
- 트랜스크립트(자막):
{transcript_text}

- 일반 시청자 댓글:
{general_text}

- 타임스탬프 기반 주요 댓글:
{timestamp_text}

"""


def load_processed_ids(output_path: str) -> set:
    """Load already-processed video IDs from output file."""
    processed = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "video_id" in data:
                        processed.add(data["video_id"])
                except Exception:
                    pass
    return processed


def main():
    parser = argparse.ArgumentParser(description="Summarize videos using EXAONE 4.0 32B via vLLM")
    parser.add_argument("--input", "-i", default="data/filtered_combined_data.jsonl", help="Input JSONL file")
    parser.add_argument("--output", "-o", default="data/summarized_data.jsonl", help="Output JSONL file")
    parser.add_argument("--host", default="http://localhost:8000/v1", help="vLLM API base URL")
    parser.add_argument("--model", default="LGAI-EXAONE/EXAONE-4.0-32B", help="Model name")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: input file not found: {args.input}")
        sys.exit(1)

    client = OpenAI(base_url=args.host, api_key="EMPTY")

    with open(args.input, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(records)} records from {args.input}")

    processed_ids = load_processed_ids(args.output)
    print(f"Already processed: {len(processed_ids)} videos — skipping")

    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)

    with open(args.output, "a", encoding="utf-8") as f_out:
        for idx, record in enumerate(records, 1):
            video_id = record.get("video_id", "")
            video_url = record.get("video_url", "")
            title = record.get("title", "")

            if video_id in processed_ids:
                print(f"[{idx}/{len(records)}] Skip (already done): {video_id}")
                continue

            transcript_text = build_transcript_text(record.get("transcript", []))
            general_text = build_comments_text(record.get("general_comments", []))
            timestamp_text = build_comments_text(record.get("timestamp_comments", []))

            if not transcript_text and general_text == "(없음)" and timestamp_text == "(없음)":
                print(f"[{idx}/{len(records)}] Skip (no content): {video_id}")
                continue

            prompt = build_prompt(transcript_text, general_text, timestamp_text)

            print(f"[{idx}/{len(records)}] Summarizing: {title[:60]}")

            max_retries = 3
            summary = None
            for attempt in range(1, max_retries + 1):
                try:
                    response = client.chat.completions.create(
                        model=args.model,
                        messages=[
                            {"role": "user", "content": prompt},
                        ],
                        temperature=args.temperature,
                        max_tokens=args.max_tokens,
                    )
                    summary = response.choices[0].message.content.strip()
                    break
                except Exception as e:
                    print(f"  ⚠ Attempt {attempt}/{max_retries} failed: {e}")
                    if attempt < max_retries:
                        time.sleep(3 * attempt)

            if summary is None:
                print(f"  ✗ All retries failed for {video_id}, skipping.")
                continue

            output_record = {
                "video_id": video_id,
                "video_url": video_url,
                "title": title,
                "channel_name": record.get("channel_name", ""),
                "summary": summary,
            }

            f_out.write(json.dumps(output_record, ensure_ascii=False) + "\n")
            f_out.flush()
            print(f"  ✓ Done.")
            breakpoint()


if __name__ == "__main__":
    main()
