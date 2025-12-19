import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_backtest(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Backtest parquet not found: {path}")
    df = pd.read_parquet(path)
    if not isinstance(df.index, pd.DatetimeIndex):
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").set_index("timestamp")
        else:
            raise ValueError("Backtest DataFrame must have DatetimeIndex or 'timestamp' column.")
    df.index = pd.to_datetime(df.index, utc=True)
    return df.sort_index()


def compute_hold_equity(df: pd.DataFrame, price_col: str, initial_capital: float = 100_000.0) -> pd.Series:
    price = df[price_col].astype(float)
    ret = price.pct_change().fillna(0.0)
    equity = (1.0 + ret).cumprod() * initial_capital
    return equity


def detect_events(df: pd.DataFrame, time_format: str) -> list[list[dict]]:
    if "position" not in df.columns:
        return [[] for _ in range(len(df))]
    pos = df["position"].to_numpy(dtype=float)
    events_per_row: list[list[dict]] = [[] for _ in range(len(df))]

    prev = 0.0
    for i, p in enumerate(pos):
        action = None
        if prev == 0.0 and p != 0.0:
            action = "BUY" if p > 0 else "SELL"
        elif prev > 0 and p <= 0:
            action = "SELL"
        elif prev < 0 and p >= 0:
            action = "BUY"
        if action is not None:
            events_per_row[i].append(
                {
                    "timestamp": format_time(df.index[i], time_format),
                    "action": action,
                    "trigger": "Sentiment strategy signal",
                }
            )
        prev = p
    return events_per_row


def format_time(ts: pd.Timestamp, time_format: str) -> str:
    ts = ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")
    if time_format.lower() == "iso":
        return ts.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return ts.strftime(time_format)


def export_backtest_json(
    backtest_parquet: Path,
    price_col: str,
    output_json: Path,
    initial_capital: float = 100_000.0,
    time_format: str = "iso",
) -> None:
    df = load_backtest(backtest_parquet)

    if "equity" not in df.columns:
        raise ValueError("Backtest parquet must contain 'equity' column from sentiment_strategy_backtest.")

    hold_equity = compute_hold_equity(df, price_col=price_col, initial_capital=initial_capital)
    strat_equity = df["equity"].astype(float) * initial_capital

    events = detect_events(df, time_format=time_format)

    records = []
    for (ts, hold_v, strat_v, evts) in zip(df.index, hold_equity, strat_equity, events):
        item = {
            "time": format_time(ts, time_format),
            "holdValue": float(hold_v),
            "strategyValue": float(strat_v),
        }
        if evts:
            item["events"] = evts
        records.append(item)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(records)} points to {output_json}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export backtest parquet to frontend JSON format")
    p.add_argument("--backtest-parquet", required=True, type=str, help="Backtest result parquet path")
    p.add_argument("--price-col", default="close", type=str, help="Price column for buy&hold benchmark")
    p.add_argument("--output-json", required=True, type=str, help="Output JSON file path")
    p.add_argument("--initial-capital", default=100_000.0, type=float, help="Initial capital for equity scaling")
    p.add_argument(
        "--time-format",
        default="iso",
        type=str,
        help="Time format for 'time' field (use 'iso' for UTC ISO 8601 with milliseconds or provide strftime pattern)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    export_backtest_json(
        backtest_parquet=Path(args.backtest_parquet),
        price_col=args.price_col,
        output_json=Path(args.output_json),
        initial_capital=args.initial_capital,
        time_format=args.time_format,
    )


if __name__ == "__main__":
    main()
