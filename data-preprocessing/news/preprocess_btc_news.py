#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
preprocess_btc_news.py

功能：
- 从 GitHub 下载 datasets/news.csv
- 打印 Raw CSV 的最新时间戳（诊断用）
- 清洗数据、去重、规范化为统一格式
- 输出 btc_news_clean.csv
"""

import io
import json
from pathlib import Path

import requests
import pandas as pd


RAW_URL = "https://raw.githubusercontent.com/mouadja02/bitcoin-news-data/main/datasets/news.csv"
OUTPUT_CSV = "btc_news_clean.csv"


def download_news_csv(url: str) -> pd.DataFrame:
    """
    从 GitHub RAW 下载 news.csv。
    """
    print(f"[INFO] Downloading BTC news from GitHub: {url}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    csv_text = resp.text
    df = pd.read_csv(io.StringIO(csv_text))
    print(f"[INFO] Downloaded raw rows: {len(df)}")

    # ---------- 新增的诊断打印 ----------
    if "DATETIME" in df.columns:
        try:
            df_dt = pd.to_datetime(df["DATETIME"], errors="coerce")
            max_dt = df_dt.max()
            min_dt = df_dt.min()
            print(f"[DIAG] Raw CSV earliest datetime : {min_dt}")
            print(f"[DIAG] Raw CSV latest datetime   : {max_dt}")
        except Exception as e:
            print(f"[DIAG] Failed to parse DATETIME in raw file: {e}")
    else:
        print("[DIAG] Raw CSV does NOT contain DATETIME column.")
    # -----------------------------------

    return df


def clean_btc_news(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗原始数据并统一格式。
    """
    expected_cols = ["DATETIME", "HEADLINE", "SUMMARY", "SOURCE", "URL", "CATEGORIES", "TAGS"]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols].copy()
    print(f"[INFO] Columns after selecting expected ones: {df.columns.tolist()}")

    # 去掉空 URL
    if "URL" in df.columns:
        before = len(df)
        df = df.dropna(subset=["URL"])
        df = df[df["URL"].astype(str).str.strip() != ""]
        print(f"[INFO] Removed {before - len(df)} rows with empty URL.")

    # URL 去重
    if "URL" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["URL"]).reset_index(drop=True)
        print(f"[INFO] Removed {before - len(df)} duplicate URLs.")

    # 解析时间
    if "DATETIME" in df.columns:
        df["datetime_utc"] = pd.to_datetime(df["DATETIME"], utc=True, errors="coerce")
    else:
        df["datetime_utc"] = pd.NaT

    before = len(df)
    df = df.dropna(subset=["datetime_utc"]).reset_index(drop=True)
    print(f"[INFO] Removed {before - len(df)} rows with invalid datetime.")

    # ---------- 新增的清洗后时间诊断 ----------
    print(f"[DIAG] After datetime cleaning, earliest = {df['datetime_utc'].min()}")
    print(f"[DIAG] After datetime cleaning, latest   = {df['datetime_utc'].max()}")
    # -----------------------------------------

    # 标题、摘要
    df["headline"] = df.get("HEADLINE", "").astype(str).fillna("").str.strip()
    df["summary"] = df.get("SUMMARY", "").astype(str).fillna("").str.strip()

    def is_informative(row):
        return (len(row["headline"]) >= 10) or (len(row["summary"]) >= 20)

    before = len(df)
    df = df[df.apply(is_informative, axis=1)].reset_index(drop=True)
    print(f"[INFO] Removed {before - len(df)} non-informative rows.")

    # 构造 text 字段
    MAX_SUMMARY_LEN = 300

    def build_text(row):
        h = row["headline"]
        s = row["summary"]
        if len(s) > MAX_SUMMARY_LEN:
            s = s[:MAX_SUMMARY_LEN] + "..."
        return f"{h}. {s}" if s else h

    df["text"] = df.apply(build_text, axis=1)

    df["source"] = df.get("SOURCE", "").astype(str).fillna("").str.strip()
    df["url"] = df.get("URL", "").astype(str).fillna("").str.strip()

    # assets=["BTC"]
    df["assets"] = df.apply(lambda _: json.dumps(["BTC"]), axis=1)

    # 排序 + id
    df = df.sort_values("datetime_utc").reset_index(drop=True)
    df["id"] = df.index.map(lambda i: f"btc_{i:06d}")

    final_cols = ["id", "datetime_utc", "headline", "summary", "text", "source", "url", "assets"]
    df_final = df[final_cols].copy()

    print(f"[INFO] Final cleaned rows: {len(df_final)}")
    return df_final


def main():
    df_raw = download_news_csv(RAW_URL)
    df_clean = clean_btc_news(df_raw)

    out_path = Path(OUTPUT_CSV)
    df_clean.to_csv(out_path, index=False)
    print(f"[INFO] Saved cleaned BTC news to: {out_path.resolve()}")

if __name__ == "__main__":
    main()
