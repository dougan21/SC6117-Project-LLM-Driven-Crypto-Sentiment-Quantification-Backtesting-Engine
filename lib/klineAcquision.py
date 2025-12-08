import ccxt
import pandas as pd
from datetime import datetime, timezone, timedelta


def get_raw_ohlcv(symbol='BTC/USDT', timeframe='5m', limit=1000):
    """
    从 Binance 获取原始 OHLCV 列表（ccxt 格式）。
    """
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    return ohlcv


def normalize_ohlcv(ohlcv, symbol='BTC/USDT', timeframe='5m'):
    """
    将原始 OHLCV 列表标准化为适合本项目使用的 DataFrame。
    """
    df = pd.DataFrame(
        ohlcv,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )

    # 1. 转换时间戳为 UTC 时间
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

    # 2. 添加元数据字段
    df['symbol'] = symbol
    df['timeframe'] = timeframe
    df['datetime'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S%z')
    df['date'] = df['timestamp'].dt.date.astype(str)

    # 3. 排序 & 去重
    df = df.sort_values('timestamp').drop_duplicates(subset=['timestamp', 'symbol'])
    df = df.reset_index(drop=True)

    # 4. 将 timestamp 设为索引（方便后续按时间切片）
    df = df.set_index('timestamp')

    return df


def get_price_data(symbol='BTC/USDT', timeframe='5m', limit=1000):
    """
    对外主函数：获取并标准化 K 线数据。
    """
    ohlcv = get_raw_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    df = normalize_ohlcv(ohlcv, symbol=symbol, timeframe=timeframe)

    print("\n=== 标准化后的第一行 K 线数据 ===")
    print(df.iloc[0])

    return df


def get_price_data_last_n_days(symbol='BTC/USDT', timeframe='5m', days=3, safety_multiplier: int = 2):
    """获取最近 N 天、指定 timeframe 的 K 线数据。

    由于交易所 API 使用 "最近 N 根" 的方式，这里通过近似估算需要的根数，
    然后再在本地按时间截取最近 N 天的数据。

    :param symbol: 交易对，例如 'BTC/USDT'
    :param timeframe: K 线周期，例如 '5m', '1h'
    :param days: 最近多少天的数据
    :param safety_multiplier: 安全系数，用于多拉一些 K 线，避免边界不足
    :return: DataFrame，index 为 UTC timestamp，仅包含最近 N 天数据
    """

    # 根据 timeframe 估算每天大约有多少根 K 线
    timeframe_map = {
        '1m': 60 * 24,
        '3m': 20 * 24,
        '5m': 12 * 24,
        '15m': 4 * 24,
        '30m': 2 * 24,
        '1h': 24,
        '4h': 6,
        '1d': 1,
    }

    per_day = timeframe_map.get(timeframe, 24)
    approx_limit = per_day * days * safety_multiplier

    df = get_price_data(symbol=symbol, timeframe=timeframe, limit=approx_limit)

    # 只保留最近 N 天
    end_ts = df.index.max()
    start_ts = end_ts - timedelta(days=days)
    df = df.loc[start_ts:end_ts]

    return df


if __name__ == "__main__":
    symbol = 'BTC/USDT'
    timeframe = '5m'
    days = 3
    df = get_price_data_last_n_days(symbol=symbol, timeframe=timeframe, days=days)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = f"kline_{symbol.replace('/', '')}_{timeframe}_last{days}d_{today_str}.parquet"
    df.to_parquet(out_path)
    print("\n=== 标准化后的第一行 K 线数据 ===")
    print(df.iloc[0])
    print(f"\n标准化后的最近 {days} 天 K 线数据已保存到: {out_path}")