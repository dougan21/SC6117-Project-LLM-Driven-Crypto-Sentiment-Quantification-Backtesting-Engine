import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd


@dataclass
class StrategyParams:
    window: int = 12  # rolling window for mean (bars)
    upper_th: float = 0.2
    lower_th: float = -0.2
    delta_th: float = 0.1
    w_trend: float = 0.7
    w_mom: float = 0.3
    max_strength: float = 0.5
    alpha: float = 0.3  # position smoothing factor
    max_drawdown: float = 0.2  # simple global risk control


def load_merged_data(path: Path, price_col: str, sentiment_col: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input parquet not found: {path}")

    df = pd.read_parquet(path)

    if not isinstance(df.index, pd.DatetimeIndex):
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").set_index("timestamp")
        else:
            raise ValueError("DataFrame must have DatetimeIndex or a 'timestamp' column.")

    df.index = pd.to_datetime(df.index, utc=True)

    if price_col not in df.columns:
        raise ValueError(f"Price column '{price_col}' not found in data.")
    if sentiment_col not in df.columns:
        raise ValueError(f"Sentiment column '{sentiment_col}' not found in data.")

    df = df.sort_index()
    return df


def build_signals(df: pd.DataFrame, sentiment_col: str, params: StrategyParams) -> pd.DataFrame:
    out = df.copy()

    sent = out[sentiment_col].astype(float).fillna(0.0)

    sent_mean = sent.rolling(params.window, min_periods=1).mean()
    sent_diff = sent_mean.diff().fillna(0.0)

    signal_trend = np.zeros(len(out), dtype=int)
    signal_trend[sent_mean.values > params.upper_th] = 1
    signal_trend[sent_mean.values < params.lower_th] = -1

    signal_mom = np.zeros(len(out), dtype=int)
    signal_mom[sent_diff.values > params.delta_th] = 1
    signal_mom[sent_diff.values < -params.delta_th] = -1

    raw = params.w_trend * signal_trend + params.w_mom * signal_mom
    direction = np.sign(raw)

    strength = np.minimum(1.0, np.abs(sent_mean.values) / params.max_strength)
    target_pos = direction * strength

    position = np.zeros(len(out), dtype=float)
    for i in range(1, len(out)):
        position[i] = params.alpha * target_pos[i] + (1.0 - params.alpha) * position[i - 1]

    out["sent_mean"] = sent_mean
    out["sent_diff"] = sent_diff
    out["direction"] = direction
    out["target_pos"] = target_pos
    out["position_raw"] = position
    return out


def apply_risk_control(df: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    out = df.copy()

    ret = out["ret"].fillna(0.0).to_numpy()
    pos = out["position_raw"].to_numpy()

    position = np.zeros_like(pos)
    equity = np.ones_like(pos)
    equity[0] = 1.0
    peak = equity[0]

    for i in range(1, len(out)):
        position[i] = pos[i]
        equity[i] = equity[i - 1] * (1.0 + position[i - 1] * ret[i])
        peak = max(peak, equity[i])
        dd = 1.0 - equity[i] / peak if peak > 0 else 0.0
        if dd > params.max_drawdown:
            position[i] = 0.0

    out["position"] = position
    out["equity"] = equity
    return out


def summarize_performance(df: pd.DataFrame, freq_per_year: int = 365 * 24 * 12) -> Dict[str, Any]:
    if "equity" not in df.columns or "ret" not in df.columns:
        raise ValueError("DataFrame must contain 'equity' and 'ret' columns for performance summary.")

    equity = df["equity"]
    ret = df["position"].shift(1).fillna(0.0) * df["ret"].fillna(0.0)

    total_return = equity.iloc[-1] - 1.0
    avg_ret = ret.mean()
    vol = ret.std()
    annualized_return = (1.0 + avg_ret) ** freq_per_year - 1.0 if avg_ret != 0 else 0.0
    annualized_vol = vol * np.sqrt(freq_per_year) if vol > 0 else 0.0
    sharpe = annualized_return / annualized_vol if annualized_vol > 0 else 0.0

    running_max = equity.cummax()
    drawdown = 1.0 - equity / running_max
    max_dd = drawdown.max()

    stats = {
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "annualized_vol": float(annualized_vol),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
    }
    return stats


def run_backtest(
    input_parquet: Path,
    price_col: str = "close",
    sentiment_col: str = "sentiment_score",
    output_path: Optional[Path] = None,
    params: Optional[StrategyParams] = None,
) -> None:
    if params is None:
        params = StrategyParams()

    df = load_merged_data(input_parquet, price_col=price_col, sentiment_col=sentiment_col)

    df["ret"] = df[price_col].pct_change().fillna(0.0)

    df_sig = build_signals(df, sentiment_col=sentiment_col, params=params)
    df_bt = apply_risk_control(df_sig, params=params)

    stats = summarize_performance(df_bt)

    print("=== Sentiment Strategy Backtest Summary ===")
    for k, v in stats.items():
        print(f"{k}: {v:.4f}")

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_bt.to_parquet(output_path)
        print(f"\nSaved backtest detail to: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sentiment-driven strategy backtest")
    parser.add_argument("--input-parquet", type=str, required=True, help="Merged price+sentiment parquet path")
    parser.add_argument("--price-col", type=str, default="close", help="Price column name")
    parser.add_argument("--sentiment-col", type=str, default="sentiment_score", help="Sentiment column name")
    parser.add_argument("--output-parquet", type=str, default=None, help="Optional path to save detailed backtest result")

    parser.add_argument("--window", type=int, default=12)
    parser.add_argument("--upper-th", type=float, default=0.2)
    parser.add_argument("--lower-th", type=float, default=-0.2)
    parser.add_argument("--delta-th", type=float, default=0.1)
    parser.add_argument("--w-trend", type=float, default=0.7)
    parser.add_argument("--w-mom", type=float, default=0.3)
    parser.add_argument("--max-strength", type=float, default=0.5)
    parser.add_argument("--alpha", type=float, default=0.3)
    parser.add_argument("--max-drawdown", type=float, default=0.2)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_parquet)
    output_path = Path(args.output_parquet) if args.output_parquet else None

    params = StrategyParams(
        window=args.window,
        upper_th=args.upper_th,
        lower_th=args.lower_th,
        delta_th=args.delta_th,
        w_trend=args.w_trend,
        w_mom=args.w_mom,
        max_strength=args.max_strength,
        alpha=args.alpha,
        max_drawdown=args.max_drawdown,
    )

    run_backtest(
        input_parquet=input_path,
        price_col=args.price_col,
        sentiment_col=args.sentiment_col,
        output_path=output_path,
        params=params,
    )


if __name__ == "__main__":
    main()
