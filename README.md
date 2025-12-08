# SC6117-Project-LLM-Driven-Crypto-Sentiment-Quantification-Backtesting-Engine

NTU SC6117 project: LLM-Driven Crypto Sentiment Quantification &amp; Backtesting Engine


## Sentiment Engine struct

```
root/
├── .env                        # openAI API key
├── run_sentiment.py            # run sentiment engine -- get sentiment score
├── config/   
│   └── scoring_strategies.json # sentiment score strategies config
├── data/   
│   ├── news_data.csv           # news input
│   ├── sentiment_results.csv   # sentiment score output
|   ├── other data file...      # ex. k line
│   └── sentiment_cache.json    # cache 
└── lib/
    ├── __init__.py
    └── sentiment_engine.py     # core for llm-sentiment-engine
```

Actually, /data only contain the code for retrieving data; it's just used here to demonstrate the file structure.

## 2025-12-08 Updates (Regression-update branch)

- Added a complete sentiment-driven backtest pipeline on top of the existing LLM sentiment engine.
- Enhanced `lib/klineAcquision.py` to fetch standardized OHLCV data for the last N days (default: last 3 days of BTC/USDT at 5m resolution) and save it as a parquet file.
- Implemented `lib/data_processor.py::SentimentAggregator.normalize_to_candles` to resample per-news sentiment scores into fixed timeframes (e.g. 5 minutes) with optional EWMA decay.
- Added `lib/prepare_dataset.py` to merge price parquet (from `klineAcquision.py`) and LLM sentiment CSV (from `run_sentiment.py`) into a unified 5-minute dataset with a `sentiment_score` factor.
- Created `lib/sentiment_strategy_backtest.py`, which defines a sentiment-based trading strategy (using sentiment mean threshold + sentiment change, with position sizing and simple drawdown-based risk control) and runs a backtest over the merged dataset, outputting an equity curve and summary statistics.
- Created `lib/export_backtest_json.py` to convert backtest results into a frontend-friendly JSON format with 5-minute points, including `time`, `holdValue`, `strategyValue`, and optional trade `events`.
- Updated `run_sentiment.py` and `lib/sentiment_engine.py` usage to clearly separate responsibilities: `run_sentiment.py` as the CLI entry point and `CryptoSentimentRunner` as the reusable LLM sentiment engine.
- Ensured the data directory structure and scripts (`klineAcquision.py`, `run_sentiment.py`, `prepare_dataset.py`, `sentiment_strategy_backtest.py`, `export_backtest_json.py`) form a coherent end-to-end pipeline: raw news + market data → LLM sentiment scores → 5m sentiment factor → backtest → JSON for UI integration.
