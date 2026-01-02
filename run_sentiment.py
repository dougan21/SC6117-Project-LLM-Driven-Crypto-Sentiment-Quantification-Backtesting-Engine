import os
import argparse
from lib.sentiment_engine import CryptoSentimentRunner, load_dotenv

# make sure to load environment variables from .env file
load_dotenv()

def run_sentiment_engine():
    """
    Process command-line arguments and start the sentiment quantification process.
    """
    
    # ----------------------------------------------------
    # 1. define & parse arguments
    # ----------------------------------------------------
    parser = argparse.ArgumentParser(
        description="LLM-Driven Crypto Sentiment Quantification Runner.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--strategy', 
        type=str, 
        default=None, 
        help="Specify the scoring strategy name to use, e.g., standard_crypto, degen_meme."
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default='./data/news_data.csv', 
        help="Input CSV file path (default: ./data/news_data.csv)"
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='./data/sentiment_results.csv', 
        help="Output CSV file path (default: ./data/sentiment_results.csv)"
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        default=None, 
        help="Limit the number of data rows to process (for testing, default: all)"
    )
    parser.add_argument(
        '--text-col', 
        type=str, 
        default='SUMMARY', 
        help="Column name for news headlines in the input CSV (default: SUMMARY)"
    )
    parser.add_argument(
        '--date-col', 
        type=str, 
        default='DATETIME', 
        help="Column name for timestamps in the input CSV (default: DATETIME)"
    )
    parser.add_argument(
        '--concurrency', 
        type=int, 
        default=1, 
        help="Concurrency level. Default is 1 (Serial). Set >1 for Async Parallel (e.g., 10)."
    )

    args = parser.parse_args()
    
    # ----------------------------------------------------
    # 2. Runner
    # ----------------------------------------------------
    print("==============================================")
    print("*** LLM-Driven Crypto Sentiment Quantification Runner ***")
    
    try:
        print(f"Initializing Runner with Strategy: {args.strategy}, Concurrency: {args.concurrency}")
        runner = CryptoSentimentRunner(
            strategy_name=args.strategy,
            concurrency=args.concurrency
        )
        
        # 3. Run task
        runner.run_csv(
            input_csv=args.input, 
            output_csv=args.output,
            text_col=args.text_col,
            date_col=args.date_col,
            limit=args.limit
        )

    except ValueError as e:
        print(f"\n start error: {e}")
        print("please check your strategy name or environment setup.")
    except Exception as e:
        print(f"\n fatal error: {e}")
        
    print("==============================================")


if __name__ == "__main__":
    run_sentiment_engine()