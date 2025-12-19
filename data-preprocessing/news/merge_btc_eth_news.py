#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
merge_btc_eth_news.py

功能：
- 读取 btc_news_clean.csv 和 eth_news_clean.csv
- 按 URL 合并去重
- 对重复新闻合并 assets，并选择“更优”的内容
- 统一重新生成 ID：news_000001, news_000002, ...
- 输出 merged_btc_eth_news.csv，字段为：

  id, datetime_utc, headline, summary, text, source, url, assets
"""

import ast
import json
import pandas as pd

INPUT_BTC = "btc_news_clean.csv"
INPUT_ETH = "eth_news_clean.csv"
OUTPUT_MERGED = "merged_btc_eth_news.csv"


def load_csv(path: str) -> pd.DataFrame:
    """读取 CSV，并把 assets 从 JSON 字符串转回 list；解析 datetime_utc。"""
    df = pd.read_csv(path)

    # 解析 assets（原来是 '["BTC"]' 这种字符串）
    if "assets" in df.columns:
        df["assets"] = df["assets"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else x
        )

    # 把 datetime_utc 转成真正的时间类型（方便排序）
    if "datetime_utc" in df.columns:
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True, errors="coerce")

    return df


def combine_assets(a1, a2):
    """合并两个资产列表并去重排序。"""
    if not isinstance(a1, list):
        a1 = [] if pd.isna(a1) else [a1]
    if not isinstance(a2, list):
        a2 = [] if pd.isna(a2) else [a2]
    return sorted(set(a1 + a2))


def pick_better_record(rec_old: dict, rec_new: dict) -> dict:
    """
    对同一 URL 的两条记录进行合并：
    - assets：并集
    - datetime_utc：取较早的（认为更接近新闻首次发布时间）
    - headline/summary/text：选更“有信息量”的版本（长度更长）
    - source：优先保留已有的；如果旧的为空、新的非空则采用新的
    其他字段如 url 保持不变。
    """
    merged = rec_old.copy()

    # 1. assets 合并
    merged["assets"] = combine_assets(rec_old.get("assets"), rec_new.get("assets"))

    # 2. datetime_utc：取较早的那个（min）
    dt1 = rec_old.get("datetime_utc")
    dt2 = rec_new.get("datetime_utc")
    if pd.notna(dt1) and pd.notna(dt2):
        merged["datetime_utc"] = min(dt1, dt2)
    elif pd.isna(dt1) and pd.notna(dt2):
        merged["datetime_utc"] = dt2
    # 如果 dt2 是 NaT，就保持 dt1 不变

    # 3. 文本相关字段：选“更长”的（更有信息量）
    for col in ["headline", "summary", "text"]:
        v1 = rec_old.get(col)
        v2 = rec_new.get(col)
        s1 = "" if v1 is None else str(v1)
        s2 = "" if v2 is None else str(v2)
        # 如果新记录的该字段更长，则用新记录的
        if len(s2) > len(s1):
            merged[col] = v2

    # 4. source：如果旧的为空（或非常短），而新的非空，则采用新的
    src_old = rec_old.get("source")
    src_new = rec_new.get("source")
    so = "" if src_old is None else str(src_old).strip()
    sn = "" if src_new is None else str(src_new).strip()
    if (not so) and sn:
        merged["source"] = src_new

    # url 不动（同一 URL 的新闻）
    return merged


def merge_news(btc_df: pd.DataFrame, eth_df: pd.DataFrame) -> pd.DataFrame:
    """按 URL 合并 BTC 与 ETH 新闻，并生成新 ID。"""

    # 只保留规范字段（避免意外多出来的列）
    keep_cols = [
        "datetime_utc",
        "headline",
        "summary",
        "text",
        "source",
        "url",
        "assets",
    ]

    btc_df = btc_df[[c for c in keep_cols if c in btc_df.columns]].copy()
    eth_df = eth_df[[c for c in keep_cols if c in eth_df.columns]].copy()

    # 合并两边数据
    df_all = pd.concat([btc_df, eth_df], ignore_index=True)

    # 确保按时间排序后再合并（方便“第一个版本”的选择更稳定）
    df_all = df_all.sort_values("datetime_utc").reset_index(drop=True)

    merged_by_url = {}

    for _, row in df_all.iterrows():
        url = row.get("url")
        if not isinstance(url, str) or not url.strip():
            # 没有 URL 的记录意义很低，可以选择忽略或特殊处理
            continue

        rec_new = row.to_dict()

        if url not in merged_by_url:
            merged_by_url[url] = rec_new
        else:
            rec_old = merged_by_url[url]
            merged_by_url[url] = pick_better_record(rec_old, rec_new)

    # 转回 DataFrame
    merged_df = pd.DataFrame(merged_by_url.values())

    # 再按时间排序
    merged_df = merged_df.sort_values("datetime_utc").reset_index(drop=True)

    # 统一生成新的 ID：news_000001 这种
    merged_df["id"] = merged_df.index.map(lambda i: f"news_{i:06d}")

    # assets 从 list 转回 JSON 字符串，保持和原 CSV 一致的风格
    merged_df["assets"] = merged_df["assets"].apply(
        lambda lst: json.dumps(sorted(set(lst)), ensure_ascii=False)
    )

    # 调整列顺序
    final_cols = [
        "id",
        "datetime_utc",
        "headline",
        "summary",
        "text",
        "source",
        "url",
        "assets",
    ]
    merged_df = merged_df[final_cols]

    return merged_df


def main():
    print("[INFO] Loading BTC CSV...")
    btc_df = load_csv(INPUT_BTC)
    print(f"[INFO] BTC rows: {len(btc_df)}")

    print("[INFO] Loading ETH CSV...")
    eth_df = load_csv(INPUT_ETH)
    print(f"[INFO] ETH rows: {len(eth_df)}")

    print("[INFO] Merging...")
    merged_df = merge_news(btc_df, eth_df)
    print(f"[INFO] Merged rows (after dedupe by URL): {len(merged_df)}")

    merged_df.to_csv(OUTPUT_MERGED, index=False)
    print(f"[INFO] Saved merged file to: {OUTPUT_MERGED}")


if __name__ == "__main__":
    main()
