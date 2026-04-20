import json
import os
import statistics

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

matplotlib.use("Agg")

_font_candidates = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/AppleGothic.ttf",
]
for _fp in _font_candidates:
    if os.path.exists(_fp):
        fm.fontManager.addfont(_fp)
        plt.rcParams["font.family"] = fm.FontProperties(fname=_fp).get_name()
        break

records = []
with open("data/filtered_combined_data.jsonl") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

general_counts = [len(r.get("general_comments", [])) for r in records]
timestamp_counts = [len(r.get("timestamp_comments", [])) for r in records]

avg_general = statistics.mean(general_counts) if general_counts else 0
avg_timestamp = statistics.mean(timestamp_counts) if timestamp_counts else 0

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("댓글 수 분포 분석", fontsize=14, fontweight="bold")

axes[0].hist(general_counts, bins=10, color="steelblue", edgecolor="white", alpha=0.85)
axes[0].axvline(avg_general, color="red", linestyle="--", linewidth=1.5, label=f"평균: {avg_general:.1f}")
axes[0].set_title("general_comments 분포")
axes[0].set_xlabel("댓글 수")
axes[0].set_ylabel("영상 수")
axes[0].legend()

axes[1].hist(timestamp_counts, bins=10, color="seagreen", edgecolor="white", alpha=0.85)
axes[1].axvline(avg_timestamp, color="red", linestyle="--", linewidth=1.5, label=f"평균: {avg_timestamp:.1f}")
axes[1].set_title("timestamp_comments 분포")
axes[1].set_xlabel("댓글 수")
axes[1].set_ylabel("영상 수")
axes[1].legend()

plt.tight_layout()
plt.savefig("data/comment_stats.png", dpi=150)

print(f"저장 완료: data/comment_stats.png")
print(f"전체 영상 수              : {len(records)}개")
print(f"general_comments 평균     : {avg_general:.1f}개")
print(f"timestamp_comments 평균   : {avg_timestamp:.1f}개")
print(f"general_comments 최솟값/최댓값  : {min(general_counts)} / {max(general_counts)}")
print(f"timestamp_comments 최솟값/최댓값: {min(timestamp_counts)} / {max(timestamp_counts)}")
