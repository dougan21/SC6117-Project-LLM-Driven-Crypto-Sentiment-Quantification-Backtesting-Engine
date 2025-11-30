import ccxt
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import time

# 配置部分
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"  # 也可以用 "4h", "1d" 
SINCE = "2025-07-17 06:00:00"
UNTIL = "2025-11-23 04:00:00"

def to_millis(dt_str):
    dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

def fetch_ohlcv_full(symbol, timeframe, since_ms, until_ms, limit=1000, verbose=True):
    exchange = ccxt.bybit()
    all_rows = []
    fetch_since = since_ms

    while True:
        if verbose:
            print(f"Fetching since: {datetime.fromtimestamp(fetch_since/1000, tz=timezone.utc)}")

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=fetch_since, limit=limit)
        if not ohlcv:
            break

        all_rows.extend(ohlcv)

        # CCXT 的返回格式一般是：
        # [ [timestamp_ms, open, high, low, close, volume], ... ]
        last_timestamp = ohlcv[-1][0]

        # 如果已经超出 until 范围，就停止
        if last_timestamp >= until_ms:
            break

        # 下一轮从最后一根K线之后继续
        fetch_since = last_timestamp + 1

        # 防止触发频率限制，稍微 sleep 一下比较保险
        time.sleep(0.2)

    # 转成 DataFrame
    df = pd.DataFrame(all_rows, columns=["timestamp_ms", "open", "high", "low", "close", "volume"])

    # 转成 tz-aware 的 UTC Datetime
    df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    df = df.drop(columns=["timestamp_ms"])

    # 只保留 until_ms 之前的
    df = df[df["timestamp"] <= pd.to_datetime(until_ms, unit="ms", utc=True)]

    # 排序 & 重置索引
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df

if __name__ == "__main__":
    since_ms = to_millis(SINCE)
    until_ms = to_millis(UNTIL)

    df_ohlcv = fetch_ohlcv_full(SYMBOL, TIMEFRAME, since_ms, until_ms)
    print(df_ohlcv.head())
    print(df_ohlcv.tail())
    print(f"Retrieve {len(df_ohlcv)} candlesticks")

    # 保存为 CSV
    out_path = Path(f"btc_usdt_{TIMEFRAME}_ohlcv.csv")
    df_ohlcv.to_csv(out_path, index=False)
    print(f"Saved to: {out_path.resolve()}")
