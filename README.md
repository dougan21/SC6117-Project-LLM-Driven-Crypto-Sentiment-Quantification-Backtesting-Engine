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
│   └── sentiment_cache.json    # cache 
└── lib/
    ├── __init__.py
    └── sentiment_engine.py     # core for llm-sentiment-engine
```
