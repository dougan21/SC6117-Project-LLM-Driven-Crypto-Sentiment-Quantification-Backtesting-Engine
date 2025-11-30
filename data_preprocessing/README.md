About the necessibility of reprocessing:

Preprocessing steps were essential to ensure the quality and reliability of sentiment features.
We removed duplicated articles, cleaned invalid text, and aligned timestamps to UTC
to prevent look-ahead bias and signal distortion.


About the necessibility of chronological alignment:

Since the raw news timestamps did not contain timezone information,
and Crypto trading data uses UTC as standard,
we interpret news timestamps as UTC (tz-aware)
to ensure strict chronological alignment and prevent look-ahead bias.


About the whole process:

raw_news.csv
    ↓ read_csv
df_raw (DataFrame)        ← clean the data
    ↓ finish cleaning
df_clean
    ↓ to_csv / write csv and JSONL
news_clean.csv / news_for_llm.jsonl