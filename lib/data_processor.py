import pandas as pd
from typing import Optional

class SentimentAggregator:
    @staticmethod
    def normalize_to_candles(
        sentiment_csv: str, 
        timeframe: str = '5T', 
        agg_method: str = 'mean',
        decay_span: Optional[int] = None
    ) -> pd.DataFrame:
        """
        output a DataFrame with sentiment scores resampled to specified timeframe.
        
        :param sentiment_csv: input CSV file path containing 'timestamp' and 'score' columns
        :param timeframe: target granularity, e.g., '1H', '4H', '5min'
        :param agg_method: aggregation method, 'mean' (recommended), 'sum', 'last'
        :param decay_span: (optional) EWMA decay span.
                           If set to 12 (and timeframe='5min'), it means sentiment influence lasts about 1 hour.
                           If not set (None), periods without news have scores directly set to zero.
        :return: normalized DataFrame (index=timestamp, col=sentiment_score)
        """
        
        # 1. Read data
        try:
            df = pd.read_csv(sentiment_csv)
        except FileNotFoundError:
            raise FileNotFoundError(f"❌ Input file not found: {sentiment_csv}")
            
        if 'timestamp' not in df.columns or 'score' not in df.columns:
            raise ValueError("CSV must contain 'timestamp' and 'score' columns")

        # 2. Preprocessing: ensure the timestamp column is datetime type and in UTC
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        
        # 3. Set index (Resample requires a time-based index)
        df.set_index('timestamp', inplace=True)
        
        # 4. Core: Resample
        # label='left', closed='left': ensure data from 10:00-10:59 is grouped into 10:00, avoiding lookahead bias
        resampler = df['score'].resample(timeframe, label='left', closed='left')
        
        # Perform aggregation
        if agg_method == 'mean':
            df_agg = resampler.mean()
        elif agg_method == 'sum':
            df_agg = resampler.sum()
        elif agg_method == 'last':
            df_agg = resampler.last()
        else:
            raise ValueError(f"Unsupported agg_method: {agg_method}")
            
        # 5. Fill NA
        # assume periods without news are "neutral" (0.0)
        df_agg = df_agg.fillna(0.0)
        
        # 6. Sentiment Decay
        # If decay_span is enabled, 0.0 will not take effect immediately, but will decay slowly from the previous score to 0
        if decay_span is not None:
            df_agg = df_agg.ewm(span=decay_span, adjust=False).mean()
        
        # 7. Finalize and return
        return df_agg.to_frame(name='sentiment_score')

# ==========================================
# Test code 
# ==========================================
# if __name__ == "__main__":
#     # 模拟生成一个测试 CSV
#     import io
#     csv_content = """timestamp,score
# 2023-10-24 10:05:00,1.0
# 2023-10-24 10:55:00,-0.2
# 2023-10-24 12:10:00,0.8"""
    
#     # 存为临时文件
#     with open("temp_test.csv", "w") as f:
#         f.write(csv_content)

#     print("--- 测试 1: 标准 1H 粒度 (无衰减) ---")
#     df_1h = SentimentAggregator.normalize_to_candles("temp_test.csv", timeframe='1H')
#     print(df_1h)
#     # 预期: 
#     # 10:00 -> 0.4 ( (1.0 - 0.2)/2 )
#     # 11:00 -> 0.0 (无新闻，归零)
#     # 12:00 -> 0.8

#     print("\n--- 测试 2: 高频 30min 粒度 (带衰减 span=2) ---")
#     df_30m = SentimentAggregator.normalize_to_candles("temp_test.csv", timeframe='30min', decay_span=2)
#     print(df_30m)
#     # 预期:
#     # 11:00 这一行虽然没新闻(原始是0)，但因为有衰减，分数不会马上变0，而是像 0.26 这样缓慢下降