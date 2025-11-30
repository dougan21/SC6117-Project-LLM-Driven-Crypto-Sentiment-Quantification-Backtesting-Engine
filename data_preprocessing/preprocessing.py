import pandas as pd
import json
from pathlib import Path

# 1. 读原始 CSV
input_path = Path("news.csv")
df = pd.read_csv(input_path)

print(f"Origin rows: {len(df)}")

# 2. 去掉 URL 完全相同的重复新闻
before = len(df)
df = df.drop_duplicates(subset=["URL"])
print(f"Rows after cleaning: {len(df)}（removed {before - len(df)}  pieces ofURL）")

# 3. 去掉标题/摘要两者都太短的行（简单防垃圾）
def is_valid(row):
    h = str(row["HEADLINE"]).strip()
    s = str(row["SUMMARY"]).strip()
    return (len(h) >= 15) or (len(s) >= 30)

before = len(df)
df = df[df.apply(is_valid, axis=1)].copy()
print(f"Rows after cleaning the short text: {len(df)}（removed {before - len(df)} pieces）")

# 4. 解析时间，并统一认为是 UTC 时间（tz-aware）
df["DATETIME"] = pd.to_datetime(df["DATETIME"], utc=True)

# 5. 排序，保证时间是单调的
df = df.sort_values("DATETIME").reset_index(drop=True)

# 6. 添加 asset 字段（目前全是 BTC，将来可扩展多币种）
df["asset"] = "BTC"

# 7. 构建给 LLM 的 text 字段：标题 + 摘要
def build_text(row):
    h = str(row["HEADLINE"]).strip()
    s = str(row["SUMMARY"]).strip()
    if s:
        return f"{h}. {s}"
    else:
        return h

df["text"] = df.apply(build_text, axis=1)

# 8. 导出“干净版 CSV”，供之后所有分析使用
clean_csv_path = Path("news_clean.csv")
df.to_csv(clean_csv_path, index=False)
print(f"saved cleaned CSV to: {clean_csv_path.resolve()}")

# 9. 导出 JSONL，方便后续批量喂给 LLM / 构建向量库
jsonl_path = Path("news_for_llm.jsonl")
with jsonl_path.open("w", encoding="utf-8") as f:
    for i, row in df.iterrows():
        rec = {
            "id": i,  # 简单用行号当 id
            "datetime_utc": row["DATETIME"].isoformat(),
            "asset": row["asset"],
            "headline": row["HEADLINE"],
            "summary": row["SUMMARY"],
            "source": row["SOURCE"],
            "url": row["URL"],
            "categories": row.get("CATEGORIES", None),
            "tags": row.get("TAGS", None),
            "text": row["text"],
        }
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Saved JSONL to: {jsonl_path.resolve()}")
