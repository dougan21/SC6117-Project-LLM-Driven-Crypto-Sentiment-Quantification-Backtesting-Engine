"""Sentiment-driven backtest pipeline extracted from Main.ipynb.

This script can be run directly:
    python main_script.py

It expects a parquet price file to exist at `example_parquet_path`.
Adjust DATA_DIR and example_parquet_path as needed.
"""

import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple, Literal

import numpy as np
import pandas as pd

# -----------------------------
# 1. Global configuration
# -----------------------------

pd.set_option("display.max_rows", 10)
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)

DATA_DIR = "./"  # adjust if your data is in a subdir


# -----------------------------
# 2. Dataclasses
# -----------------------------


@dataclass
class BacktestConfig:
    """Configuration for sentiment-driven trading backtest."""

    symbol: str
    fee_rate: float = 0.001
    allow_short: bool = True
    max_position_holding_bars: Optional[int] = None
    sentiment_long_threshold: float = 0.5
    sentiment_short_threshold: float = -0.5
    initial_capital: float = 100_000.0
    price_column: str = "close"


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark (buy & hold) backtest."""

    symbol: str
    price_column: str = "close"


@dataclass
class TradeRecord:
    """Single trade record."""

    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: int  # 1 for long, -1 for short
    entry_price: float
    exit_price: float
    pnl: float
    return_pct: float


@dataclass
class BacktestStats:
    """Summary statistics for a backtest."""

    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int


@dataclass
class BacktestResult:
    """Detailed backtest result including equity curve and trades."""

    equity_curve: pd.Series
    trades: List[TradeRecord]
    stats: BacktestStats


@dataclass
class BacktestCurve:
    """Wrapper for equity curve with metadata for plotting."""

    symbol: str
    curve: pd.Series
    label: str


@dataclass
class StrategyVsBenchmark:
    """Comparison between strategy and benchmark results."""

    strategy: BacktestResult
    benchmark: BacktestResult
    strategy_curve: BacktestCurve
    benchmark_curve: BacktestCurve


@dataclass
class BacktestOutput:
    """High-level backtest output for front-end visualization."""

    symbol: str
    timeframe: str
    comparison: StrategyVsBenchmark
    extra_info: Optional[Dict[str, Any]] = None


# -----------------------------
# 3. Load price data from parquet
# -----------------------------


def load_price_data_from_parquet(filepath: str, price_column: str = "close") -> pd.DataFrame:
    """Load standardized OHLCV price data from a parquet file.

    Returns a DataFrame with DatetimeIndex.
    """

    df = pd.read_parquet(filepath)

    if "timestamp" in df.columns:
        df = df.sort_values("timestamp")
        df = df.set_index("timestamp")

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)

    if price_column not in df.columns:
        raise ValueError(f"Price column '{price_column}' not found in DataFrame.")

    return df


# -----------------------------
# 4. Simulate random sentiment
# -----------------------------


def simulate_random_sentiment(
    price_df: pd.DataFrame,
    symbol: str,
    mu: float = 0.0,
    sigma: float = 0.5,
    seed: Optional[int] = 42,
) -> pd.DataFrame:
    """Simulate random sentiment time series aligned with price index."""

    if seed is not None:
        np.random.seed(seed)

    n = len(price_df)
    sentiments = np.random.normal(loc=mu, scale=sigma, size=n)

    sentiment_df = pd.DataFrame(
        {
            "symbol": symbol,
            "sentiment": sentiments,
        },
        index=price_df.index,
    )
    sentiment_df.index.name = "timestamp"
    return sentiment_df


def simulate_sparse_random_sentiment_by_hours(
    price_df: pd.DataFrame,
    symbol: str,
    mu: float = 0.0,
    sigma: float = 0.5,
    min_hours: float = 3.0,
    max_hours: float = 5.0,
    seed: Optional[int] = 42,
) -> pd.DataFrame:
    """Simulate sparse random sentiment points every ~3-5 hours.

    The output is a *sparse* sentiment DataFrame (much lower frequency
    than the price bars). Later, `align_price_and_sentiment` will
    backward-fill these points onto each price bar so that the
    backtest still runs at the full price frequency.
    """

    if seed is not None:
        np.random.seed(seed)

    if min_hours <= 0 or max_hours <= 0 or max_hours < min_hours:
        raise ValueError("min_hours and max_hours must be positive and max_hours >= min_hours.")

    if len(price_df.index) == 0:
        raise ValueError("price_df must have at least one row.")

    start_ts = price_df.index[0]
    end_ts = price_df.index[-1]

    sparse_times: list[pd.Timestamp] = []
    current_ts = start_ts

    # 在 [min_hours, max_hours] 区间内随机步进，直到超过最后一个时间点
    while current_ts <= end_ts:
        sparse_times.append(current_ts)
        delta_hours = np.random.uniform(min_hours, max_hours)
        current_ts = current_ts + pd.Timedelta(hours=float(delta_hours))

    # 生成与稀疏时间点等长的情绪序列
    n = len(sparse_times)
    sentiments = np.random.normal(loc=mu, scale=sigma, size=n)

    sentiment_df = pd.DataFrame(
        {
            "symbol": symbol,
            "sentiment": sentiments,
        },
        index=pd.DatetimeIndex(sparse_times, tz=start_ts.tz),
    )
    sentiment_df.index.name = "timestamp"
    return sentiment_df


# -----------------------------
# 5 & 7. Sentiment normalization, alignment and signal generation
# -----------------------------


def normalize_sentiment_df(sentiment_df: pd.DataFrame, default_symbol: Optional[str] = None) -> pd.DataFrame:
    """Normalize sentiment DataFrame schema.

    Expected output schema:
        index: DatetimeIndex named 'timestamp'
        columns: at least ['symbol', 'sentiment']
    """

    df = sentiment_df.copy()

    if not isinstance(df.index, pd.DatetimeIndex):
        if "timestamp" in df.columns:
            df = df.set_index("timestamp")
        else:
            raise ValueError("Sentiment DataFrame must have DatetimeIndex or 'timestamp' column.")

    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "timestamp"

    if "symbol" not in df.columns:
        if default_symbol is None:
            raise ValueError("Sentiment DataFrame has no 'symbol' column and no default_symbol provided.")
        df["symbol"] = default_symbol

    if "sentiment" not in df.columns:
        if "score" in df.columns:
            df["sentiment"] = df["score"].astype(float)
        else:
            raise ValueError("Sentiment DataFrame must have a 'sentiment' or 'score' column.")

    return df.sort_index()


def align_price_and_sentiment(
    price_df: pd.DataFrame,
    sentiment_df: pd.DataFrame,
    symbol: Optional[str] = None,
    *,
    apply_time_decay: bool = False,
    decay_half_life_hours: float = 6.0,
) -> pd.DataFrame:
    """Align price and sentiment by timestamp using backward merge (no look-ahead).

    If ``apply_time_decay`` is True, the sentiment value will be
    decayed as time passes since the last sentiment update, using a
    simple exponential half-life model over ``decay_half_life_hours``.
    """

    price = price_df.copy()
    sentiment = normalize_sentiment_df(sentiment_df, default_symbol=symbol)

    if symbol is not None:
        if "symbol" in price.columns:
            price = price[price["symbol"] == symbol]
        sentiment = sentiment[sentiment["symbol"] == symbol]

    price = price.sort_index()
    sentiment = sentiment.sort_index()

    merged = pd.merge_asof(
        left=price.reset_index().rename(columns={"index": "timestamp"}),
        right=sentiment.reset_index().rename(columns={"index": "timestamp"}),
        on="timestamp",
        by=None,
        direction="backward",
    )

    merged = merged.set_index("timestamp")
    merged.index = pd.to_datetime(merged.index, utc=True)
    # 可选：对情绪做时间衰减
    if apply_time_decay:
        if "sentiment" not in merged.columns:
            raise ValueError("Merged DataFrame must contain 'sentiment' column for decay.")

        if decay_half_life_hours <= 0:
            raise ValueError("decay_half_life_hours must be positive when apply_time_decay is True.")

        # 记录每个价格时间点对应的“最近一次情绪更新时间”
        # merge_asof 已经帮我们完成 backward 对齐，这里只需用 sentiment_df 的索引重新做一次对齐
        sentiment_ts = sentiment.index
        if len(sentiment_ts) == 0:
            return merged

        # 找到每个价格时间点对应的上一次情绪时间
        # 使用 merge_asof 的思想：对时间戳做 backward 匹配
        price_times = merged.index
        # pandas 没有直接给出“上一次时间戳”的列，这里手工实现：
        # 对 sentiment_ts 进行索引搜索，找到 <= t 的最后一个索引位置
        sentiment_ts_np = sentiment_ts.view("int64")
        price_ts_np = price_times.view("int64")

        last_sent_ts_for_price = []
        import numpy as _np  # 局部导入，避免污染命名空间太多

        for t_int in price_ts_np:
            pos = _np.searchsorted(sentiment_ts_np, t_int, side="right") - 1
            if pos < 0:
                # 没有历史情绪点，就认为没有情绪（衰减后为 0）
                last_sent_ts_for_price.append(_np.nan)
            else:
                last_sent_ts_for_price.append(sentiment_ts_np[pos])

        last_sent_ts_for_price = _np.array(last_sent_ts_for_price)

        # 计算每个 bar 相对最近情绪更新时间的时间差（小时）
        # 注意：NaN 表示没有情绪来源，我们将对应情绪直接置为 0
        valid_mask = ~_np.isnan(last_sent_ts_for_price)
        dt_hours = _np.zeros_like(price_ts_np, dtype=float)
        dt_hours[~valid_mask] = _np.inf

        # 只对有情绪来源的点计算时间差
        dt_int = price_ts_np[valid_mask] - last_sent_ts_for_price[valid_mask]
        dt_hours[valid_mask] = dt_int / (1e9 * 60 * 60)  # ns -> hours

        # 指数衰减因子：decay_factor = 0.5 ** (dt / half_life)
        half_life = float(decay_half_life_hours)
        decay_factor = _np.power(0.5, dt_hours / half_life)
        # 没有情绪来源的点，衰减因子视为 0
        decay_factor[~valid_mask] = 0.0

        # 应用衰减
        merged["sentiment"] = merged["sentiment"].astype(float) * decay_factor

    return merged


def generate_trading_signals(merged_df: pd.DataFrame, config: BacktestConfig) -> pd.Series:
    """Generate long/short/flat trading signals based on sentiment."""

    if "sentiment" not in merged_df.columns:
        raise ValueError("merged_df must contain a 'sentiment' column to generate signals.")

    sentiment = merged_df["sentiment"].astype(float)

    long_th = config.sentiment_long_threshold
    short_th = config.sentiment_short_threshold

    signal = pd.Series(0, index=merged_df.index, dtype=int)

    signal[sentiment > long_th] = 1
    if config.allow_short:
        signal[sentiment < short_th] = -1
    else:
        signal[sentiment < short_th] = 0

    return signal


# -----------------------------
# 6. Load LLM sentiment from CSV (optional utility)
# -----------------------------


def load_sentiment_from_csv(
    csv_path: str,
    symbol: str,
    timestamp_col: str = "timestamp",
) -> pd.DataFrame:
    """Load sentiment results from a CSV file produced by the LLM pipeline."""

    df = pd.read_csv(csv_path)

    if timestamp_col not in df.columns:
        raise ValueError(f"Timestamp column '{timestamp_col}' not found in sentiment CSV.")

    df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True, errors="coerce")
    df = df.dropna(subset=[timestamp_col])
    df = df.set_index(timestamp_col)
    df.index.name = "timestamp"

    if "score" not in df.columns:
        raise ValueError("Sentiment CSV must contain a 'score' column.")

    df["sentiment"] = df["score"].astype(float)
    df["symbol"] = symbol

    for col in ["headline", "reason"]:
        if col not in df.columns:
            df[col] = None

    return df.sort_index()


# -----------------------------
# 8. Backtest execution and statistics
# -----------------------------


def execute_backtest(price_df: pd.DataFrame, signal: pd.Series, config: BacktestConfig) -> BacktestResult:
    """Execute a simple bar-by-bar backtest using sentiment-based signals."""

    signal = signal.reindex(price_df.index).fillna(0).astype(int)

    price_col = config.price_column
    if price_col not in price_df.columns:
        raise ValueError(f"Price column '{price_col}' not found in price DataFrame.")

    prices = price_df[price_col].astype(float)

    equity: List[float] = []
    times: List[pd.Timestamp] = []
    trades: List[TradeRecord] = []

    cash = config.initial_capital
    position = 0
    entry_price: Optional[float] = None
    entry_time: Optional[pd.Timestamp] = None

    prev_signal = 0

    for t, price in prices.items():
        current_signal = signal.loc[t]

        if current_signal != prev_signal:
            if position != 0 and entry_price is not None and entry_time is not None:
                notional = cash
                if position == 1:
                    ret = price / entry_price - 1.0
                else:
                    ret = entry_price / price - 1.0

                pnl = notional * ret

                fee = abs(notional) * config.fee_rate
                cash = cash + pnl - fee

                trades.append(
                    TradeRecord(
                        entry_time=entry_time,
                        exit_time=t,
                        direction=position,
                        entry_price=float(entry_price),
                        exit_price=float(price),
                        pnl=float(pnl - fee),
                        return_pct=float(ret),
                    )
                )

                position = 0
                entry_price = None
                entry_time = None

            if current_signal != 0:
                position = int(current_signal)
                entry_price = price
                entry_time = t

                fee_open = cash * config.fee_rate
                cash -= fee_open

        if position == 0 or entry_price is None:
            equity_value = cash
        else:
            notional = cash
            if position == 1:
                ret = price / entry_price - 1.0
            else:
                ret = entry_price / price - 1.0
            equity_value = cash + notional * ret

        times.append(t)
        equity.append(equity_value)
        prev_signal = current_signal

    equity_series = pd.Series(equity, index=pd.DatetimeIndex(times, tz="UTC"))

    stats = compute_backtest_stats(equity_series, trades)

    return BacktestResult(equity_curve=equity_series, trades=trades, stats=stats)


def _estimate_bars_per_year(index: pd.DatetimeIndex) -> float:
    """Estimate how many bars per year based on the index frequency."""

    if len(index) < 2:
        return 252.0

    total_days = (index[-1] - index[0]).total_seconds() / (3600 * 24)
    if total_days <= 0:
        return 252.0

    bars_per_day = len(index) / total_days
    return bars_per_day * 252.0


def compute_backtest_stats(equity_curve: pd.Series, trades: List[TradeRecord]) -> BacktestStats:
    """Compute basic performance statistics from equity curve and trades."""

    equity_curve = equity_curve.sort_index()
    returns = equity_curve.pct_change().dropna()

    if len(equity_curve) == 0:
        return BacktestStats(
            total_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            num_trades=0,
        )

    total_return = float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1.0)

    bars_per_year = _estimate_bars_per_year(equity_curve.index)

    avg_ret = returns.mean()
    vol = returns.std()

    if vol > 0:
        sharpe = float((avg_ret * bars_per_year**0.5) / vol)
    else:
        sharpe = 0.0

    annualized_return = float((1.0 + avg_ret) ** bars_per_year - 1.0)
    volatility = float(vol * (bars_per_year**0.5))

    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0
    max_drawdown = float(drawdown.min())

    num_trades = len(trades)
    if num_trades > 0:
        wins = [1 for tr in trades if tr.pnl > 0]
        win_rate = float(len(wins) / num_trades)
    else:
        win_rate = 0.0

    return BacktestStats(
        total_return=total_return,
        annualized_return=annualized_return,
        volatility=volatility,
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        num_trades=num_trades,
    )


# -----------------------------
# 9. Benchmark buy & hold
# -----------------------------


def run_benchmark_buy_and_hold(
    price_df: pd.DataFrame,
    config: BenchmarkConfig,
    initial_capital: float,
) -> BacktestResult:
    """Run a simple buy-and-hold benchmark strategy."""

    price_col = config.price_column
    if price_col not in price_df.columns:
        raise ValueError(f"Price column '{price_col}' not found in DataFrame.")

    prices = price_df[price_col].astype(float).sort_index()

    if len(prices) == 0:
        empty_equity = pd.Series([], dtype=float)
        empty_trades: List[TradeRecord] = []
        stats = compute_backtest_stats(empty_equity, empty_trades)
        return BacktestResult(empty_equity, empty_trades, stats)

    entry_time = prices.index[0]
    entry_price = prices.iloc[0]

    qty = initial_capital / entry_price

    equity = qty * prices

    exit_time = prices.index[-1]
    exit_price = prices.iloc[-1]

    pnl = qty * (exit_price - entry_price)
    ret_pct = float(exit_price / entry_price - 1.0)

    trade = TradeRecord(
        entry_time=entry_time,
        exit_time=exit_time,
        direction=1,
        entry_price=float(entry_price),
        exit_price=float(exit_price),
        pnl=float(pnl),
        return_pct=ret_pct,
    )

    stats = compute_backtest_stats(equity, [trade])

    return BacktestResult(equity_curve=equity, trades=[trade], stats=stats)


# -----------------------------
# 10. Build chart datapoints
# -----------------------------


def _choose_time_granularity(index: pd.DatetimeIndex) -> Literal["hour", "day", "week"]:
    """Choose time granularity based on number of data points."""

    n = len(index)
    if n <= 24:
        return "hour"
    if n <= 30:
        return "day"
    return "week"


def build_chart_datapoints_from_output(output: BacktestOutput) -> list[dict]:
    """Build chart datapoints for front-end from BacktestOutput."""

    strategy_curve = output.comparison.strategy.equity_curve.sort_index()
    bench_curve = output.comparison.benchmark.equity_curve.sort_index()

    joined = pd.concat([strategy_curve, bench_curve], axis=1, join="inner")
    joined.columns = ["strategy_equity", "benchmark_equity"]

    s0 = joined["strategy_equity"].iloc[0]
    b0 = joined["benchmark_equity"].iloc[0]

    strategy_ret = joined["strategy_equity"] / s0 - 1.0
    benchmark_ret = joined["benchmark_equity"] / b0 - 1.0

    granularity = _choose_time_granularity(joined.index)

    if granularity == "hour":
        rule = "1H"
    elif granularity == "day":
        rule = "1D"
    else:
        rule = "W-MON"

    strategy_ret_rs = strategy_ret.resample(rule).last().dropna()
    benchmark_ret_rs = benchmark_ret.resample(rule).last().dropna()

    ret_df = pd.concat([strategy_ret_rs, benchmark_ret_rs], axis=1, join="inner")
    ret_df.columns = ["strategy_ret", "benchmark_ret"]

    datapoints: list[dict] = []

    for ts, row in ret_df.iterrows():
        s_ret = float(row["strategy_ret"])
        b_ret = float(row["benchmark_ret"])
        diff = s_ret - b_ret

        if granularity == "hour":
            time_str = ts.strftime("%H:00")
        elif granularity == "day":
            time_str = ts.strftime("%Y-%m-%d")
        else:
            time_str = "Week of " + ts.strftime("%Y-%m-%d")

        datapoints.append(
            {
                "time": time_str,
                "realPrice": b_ret,
                "predictionPrice": s_ret,
                "percentDifference": diff,
            }
        )

    return datapoints


# -----------------------------
# 11. Top-level runner combining strategy and benchmark
# -----------------------------


def run_backtest_with_benchmark(
    price_df: pd.DataFrame,
    sentiment_df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    strategy_config: BacktestConfig,
) -> BacktestOutput:
    """Run sentiment-driven strategy and benchmark, and pack results together."""

    merged = align_price_and_sentiment(
        price_df,
        sentiment_df,
        symbol=None,
        apply_time_decay=True,
        decay_half_life_hours=6.0,
    )

    signal = generate_trading_signals(merged, strategy_config)

    strategy_result = execute_backtest(merged, signal, strategy_config)

    benchmark_cfg = BenchmarkConfig(symbol=symbol, price_column=strategy_config.price_column)
    benchmark_result = run_benchmark_buy_and_hold(
        price_df=price_df,
        config=benchmark_cfg,
        initial_capital=strategy_config.initial_capital,
    )

    strategy_curve = BacktestCurve(
        symbol=symbol,
        curve=strategy_result.equity_curve,
        label=f"Sentiment strategy ({timeframe})",
    )

    benchmark_curve = BacktestCurve(
        symbol=symbol,
        curve=benchmark_result.equity_curve,
        label=f"Buy & Hold ({timeframe})",
    )

    comparison = StrategyVsBenchmark(
        strategy=strategy_result,
        benchmark=benchmark_result,
        strategy_curve=strategy_curve,
        benchmark_curve=benchmark_curve,
    )

    return BacktestOutput(
        symbol=symbol,
        timeframe=timeframe,
        comparison=comparison,
        extra_info=None,
    )


# -----------------------------
# 12. Script entry point: demo run
# -----------------------------


def main() -> None:
    """Simple demo: run backtest with random sentiment if parquet exists."""

    example_parquet_path = os.path.join(
        DATA_DIR,
        "kline_BTCUSDT_1m_2025-12-01.parquet",  # adjust to your actual file
    )

    if not os.path.exists(example_parquet_path):
        print(
            "Parquet file not found:",
            example_parquet_path,
            "\nPlease update 'example_parquet_path' in main_script.py to point to your price data.",
        )
        return

    price_df = load_price_data_from_parquet(example_parquet_path, price_column="close")

    # 使用稀疏情绪：大约每 3-5 小时产生一个新的情绪点
    # 回测仍然按原始价格频率逐 bar 运行，
    # 通过 align_price_and_sentiment 进行 backward 对齐。
    demo_sentiment = simulate_sparse_random_sentiment_by_hours(
        price_df,
        symbol="BTC/USDT",
        mu=0.0,
        sigma=0.5,
        min_hours=3.0,
        max_hours=5.0,
        seed=42,
    )

    demo_config = BacktestConfig(
        symbol="BTC/USDT",
        fee_rate=0.001,
        allow_short=True,
        sentiment_long_threshold=0.5,
        sentiment_short_threshold=-0.5,
        initial_capital=100_000.0,
        price_column="close",
    )

    output = run_backtest_with_benchmark(
        price_df=price_df,
        sentiment_df=demo_sentiment,
        symbol="BTC/USDT",
        timeframe="1m",
        strategy_config=demo_config,
    )

    print("Sentiment strategy stats:")
    print(output.comparison.strategy.stats)
    print("\nBenchmark stats:")
    print(output.comparison.benchmark.stats)
    print(
        "Backtest range:",
        price_df.index[0],
        "to",
        price_df.index[-1],
    )
    print("Number of sentiment strategy trades:", len(output.comparison.strategy.trades))

    chart_data = build_chart_datapoints_from_output(output)
    print("\nFirst 5 chart datapoints:")
    for point in chart_data[:5]:
        print(point)


if __name__ == "__main__":
    main()
