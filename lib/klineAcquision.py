import ccxt
import pandas as pd
from datetime import datetime, timezone, timedelta
import argparse


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


def parse_hourly_datetime(dt_str: str) -> datetime:
    """将字符串解析为整点 UTC 时间。

    支持示例格式：
    - "2025-12-01 08"
    - "2025-12-01 08:00"
    - "2025-12-01T08:00"

    如果没有时区信息，则假定为 UTC。
    最终会向下取整到整点（小时）。
    """
    ts = pd.to_datetime(dt_str, utc=True)
    # 向下取整到整点
    ts = ts.floor('H')
    return ts.to_pydatetime()


def get_price_data_range(
    symbol: str,
    timeframe: str,
    start_time: datetime,
    end_time: datetime,
    limit_per_call: int = 1000,
):
    """获取指定时间范围内的 K 线数据，时间跨度不做限制。

    :param symbol: 交易对，例如 'BTC/USDT'
    :param timeframe: K 线周期，例如 '5m', '1h'
    :param start_time: 起始时间（UTC，整点）
    :param end_time: 结束时间（UTC，整点）
    :param limit_per_call: 每次 API 请求的最大根数（由交易所限制，通常 1000 左右）
    :return: DataFrame，index 为 UTC timestamp，仅包含 [start_time, end_time] 范围内的数据
    """

    if end_time <= start_time:
        raise ValueError("end_time 必须晚于 start_time")

    exchange = ccxt.binance()

    start_ms = int(start_time.replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(end_time.replace(tzinfo=timezone.utc).timestamp() * 1000)

    all_ohlcv = []
    since = start_ms

    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit_per_call)
        if not ohlcv:
            break

        all_ohlcv.extend(ohlcv)

        last_ts = ohlcv[-1][0]

        # 如果已经覆盖到结束时间，或者返回条数少于 limit_per_call，说明已经没有更多数据
        if last_ts >= end_ms or len(ohlcv) < limit_per_call:
            break

        # 下一个请求从上一根 K 线之后开始，避免重复
        since = last_ts + 1

    if not all_ohlcv:
        raise ValueError("在指定时间范围内未获取到任何 K 线数据，请检查时间范围或交易对。")

    df = normalize_ohlcv(all_ohlcv, symbol=symbol, timeframe=timeframe)

    # 最终只保留 [start_time, end_time] 区间内的数据
    df = df.loc[(df.index >= start_time) & (df.index <= end_time)]

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 Binance 获取 K 线数据并保存为 parquet 文件")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="交易对，例如 BTC/USDT")
    parser.add_argument("--timeframe", type=str, default="5m", help="K 线周期，例如 5m, 1h")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--days", type=int, help="最近 N 天的数据（兼容旧逻辑）")
    group.add_argument("--start", type=str, help="起始时间（UTC），小时粒度，例如 2025-12-01 08 或 2025-12-01T08:00")

    parser.add_argument("--end", type=str, help="结束时间（UTC），小时粒度，例如 2025-12-03 08 或 2025-12-03T08:00")
    parser.add_argument("--out", type=str, default=None, help="输出 parquet 文件路径（可选）")

    args = parser.parse_args()

    symbol = args.symbol
    timeframe = args.timeframe

    # 兼容模式：仅提供 days，则使用“最近 N 天”逻辑
    if args.days is not None and args.start is None and args.end is None:
        days = args.days
        df = get_price_data_last_n_days(symbol=symbol, timeframe=timeframe, days=days)

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_path = args.out or f"kline_{symbol.replace('/', '')}_{timeframe}_last{days}d_{today_str}.parquet"
    else:
        if not args.start or not args.end:
            raise SystemExit("必须同时提供 --start 和 --end，或者只提供 --days。")

        start_time = parse_hourly_datetime(args.start)
        end_time = parse_hourly_datetime(args.end)

        df = get_price_data_range(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
        )

        start_str = start_time.strftime("%Y%m%dT%H")
        end_str = end_time.strftime("%Y%m%dT%H")
        out_path = args.out or f"kline_{symbol.replace('/', '')}_{timeframe}_{start_str}_{end_str}.parquet"

    df.to_parquet(out_path)
    print("\n=== 标准化后的第一行 K 线数据 ===")
    print(df.iloc[0])
    print(f"\n共获取 {len(df)} 根 K 线，已保存到: {out_path}")