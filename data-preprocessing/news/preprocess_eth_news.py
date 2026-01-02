#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
preprocess_eth_news.py

功能：
- 从 CryptoNews API 拉取 ETH 新闻
- 清洗、去重、统一成 UTC
- 输出 eth_news_clean.csv（结构与 BTC 完全一致）

最终保留 8 个字段：
id, datetime_utc, headline, summary, text, source, url, assets
"""

import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional


# ======================
# 配置开关
# ======================

# 当前处于 trial → True（每次只能取 3 条）
# 激活正式套餐后改成 False
USE_TRIAL = True

# API endpoint & 参数
BASE_URL = "https://cryptonews-api.com/api/v1"
TICKER = "ETH"
DATE_FILTER = "yeartodate"
OUTPUT_CSV = "eth_news_clean.csv"

# Trial 限制
ITEMS_TRIAL = 3
MAX_PAGES_TRIAL = 3

# 正式套餐限制
ITEMS_PAID = 100
MAX_PAGES_PAID = 10


# ======================
# 工具函数
# ======================

def load_api_key() -> str:
    """从 .env 中读取 API key"""
    load_dotenv()
    api_key = os.getenv("CRYPTONEWS_API_KEY")
    if not api_key:
        raise RuntimeError("未找到 CRYPTONEWS_API_KEY，请在 .env 中设置")
    return api_key


def fetch_eth_news_page(
    api_key: str,
    page: int,
    items: int,
    date_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """抓取某一页 ETH 新闻"""

    params = {
        "tickers": TICKER,
        "items": items,
        "page": page,
        "type": "article",
        "token": api_key,
    }

    if date_filter:
        params["date"] = date_filter

    print(f"[INFO] Fetching page={page}, items={items} ...")
    resp = requests.get(BASE_URL, params=params, timeout=20)

    if resp.status_code != 200:
        print(f"[ERROR] Status {resp.status_code}, body: {resp.text}")
        resp.raise_for_status()

    data = resp.json()
    articles = data.get("data", [])

    if not isinstance(articles, list):
        print("[WARN] Response format error: 'data' not list")
        return []

    return articles


def fetch_all_eth_news(api_key: str) -> List[Dict[str, Any]]:
    """按 Trial / 正式套餐抓取全部 ETH 新闻"""

    if USE_TRIAL:
        items = ITEMS_TRIAL
        max_pages = MAX_PAGES_TRIAL
        print(f"[INFO] Trial mode: items={items}, max_pages={max_pages}")
    else:
        items = ITEMS_PAID
        max_pages = MAX_PAGES_PAID
        print(f"[INFO] Paid mode: items={items}, max_pages={max_pages}")

    all_articles = []

    for page in range(1, max_pages + 1):
        try:
            articles = fetch_eth_news_page(api_key, page, items, DATE_FILTER)
        except Exception as e:
            print(f"[ERROR] Page {page} error: {e}")
            break

        if not articles:
            print(f"[INFO] Page {page} returned 0 articles. Stop.")
            break

        print(f"[INFO] Page {page}: {len(articles)} articles")
        all_articles.extend(articles)

        if len(articles) < items:
            print("[INFO] Last page reached (return < items).")
            break

        time.sleep(1)

    print(f"[INFO] Total articles fetched: {len(all_articles)}")
    return all_articles


def normalize_datetime_utc(series: pd.Series) -> pd.Series:
    """将 date 转为 UTC"""
    dt = pd.to_datetime(series, errors="coerce", utc=True)
    if dt.isna().sum() > 0:
        print(f"[WARN] {dt.isna().sum()} rows have invalid datetime.")
    return dt


def transform_to_dataframe(articles: List[Dict[str, Any]]) -> pd.DataFrame:
    """将 raw JSON 转为统一格式 DataFrame"""

    if not articles:
        return pd.DataFrame()

    raw = pd.DataFrame(articles)
    df = pd.DataFrame()

    df["datetime_utc"] = normalize_datetime_utc(raw.get("date"))
    df["source"] = raw.get("source_name")
    df["headline"] = raw.get("title")
    df["text"] = raw.get("text")
    df["text"] = df["text"].fillna(df["headline"])
    df["summary"] = df["text"]
    df["url"] = raw.get("news_url")
    df["assets"] = df.apply(lambda r: ["ETH"], axis=1)

    # 排序
    df = df.sort_values("datetime_utc").reset_index(drop=True)
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """按 URL + headline 去重"""
    before = len(df)
    df = df.drop_duplicates(subset=["url", "headline"], keep="first").reset_index(drop=True)
    print(f"[INFO] Deduplicated: {before} -> {len(df)}")
    return df


def save_to_csv(df: pd.DataFrame, path: str):
    """保存最终 CSV，只保留 8 个字段"""

    if df.empty:
        print("[WARN] Empty DataFrame. Skip save.")
        return

    df = df.sort_values("datetime_utc").reset_index(drop=True)
    df["id"] = df.index.map(lambda i: f"eth_{i:06d}")

    df["assets"] = df["assets"].apply(lambda x: json.dumps(x, ensure_ascii=False))

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

    df = df[final_cols]

    df.to_csv(path, index=False)
    print(f"[INFO] Saved cleaned ETH news to {path}")


def main():
    api_key = load_api_key()

    articles = fetch_all_eth_news(api_key)
    if not articles:
        print("[WARN] No articles fetched.")
        return

    df = transform_to_dataframe(articles)
    df = drop_duplicates(df)
    save_to_csv(df, OUTPUT_CSV)
    print("[INFO] Done.")


if __name__ == "__main__":
    main()
