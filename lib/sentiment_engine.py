import pandas as pd
import json
import os
import hashlib
from dotenv import load_dotenv
from typing import Dict, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# ==========================================
# 0. initialize API Key
# ==========================================
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("API Key Not Found!")

# ==========================================
# 1. Pydantic Structure
# ==========================================
class SentimentResult(BaseModel):
    score: float = Field(description="Sentiment score between -1.0 and 1.0.")
    reasoning: str = Field(description="Brief reason, max 1 sentence.")

# ==========================================
# 2. Strategy + Cache + Sentiment Engine
# ==========================================
class CryptoSentimentRunner:
    def __init__(self, 
                 strategy_name: Optional[str] = None, 
                 config_file: str = "./config/scoring_strategies.json",
                 cache_file: str = "./data/sentiment_cache.json",
                 model: str = "gpt-4o-mini"):
                #  model: str = "Qwen/Qwen2.5-7B-Instruct"):
        
        self.config_file = config_file
        self.cache_file = cache_file
        
        # 1. Load strategy rules
        # self.current_strategy_name is used to generate cache Hash to distinguish different strategies
        self.rules_text, self.current_strategy_name = self._load_strategy_rules(strategy_name)
        
        # 2. Load local cache (result cache)
        self.cache = self._load_cache()
        
        # 3. Initialize LangChain components
        self.parser = PydanticOutputParser(pydantic_object=SentimentResult)
        self.llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)
        
        template = """
        You are a crypto quantitative researcher. Analyze the immediate market sentiment.
        
        Current Scoring Strategy: "{strategy_name}"
        Rules:
        {scoring_rules}

        Output Requirements:
        {format_instructions}

        Headline: {headline}
        """
        
        self.prompt = ChatPromptTemplate.from_template(template).partial(
            strategy_name=self.current_strategy_name,
            scoring_rules=self.rules_text,
            format_instructions=self.parser.get_format_instructions()
        )
        
        self.chain = self.prompt | self.llm | self.parser

    # --- Strategy Loading Logic ---
    def _load_strategy_rules(self, strategy_name):
        """Read strategy configuration file"""
        if not os.path.exists(self.config_file):
            print("Config not found, using default fallback.")
            return "- 1.0: Good\n- -1.0: Bad", "default_fallback"

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Determine strategy name
        if not strategy_name:
            strategy_name = config.get("default_strategy", "standard_crypto")
            
        print(f"Using Strategy: [{strategy_name}]")
        
        rules = config["strategies"].get(strategy_name, [])
        if not rules:
            raise ValueError(f"Strategy '{strategy_name}' not found!")

        # Format rules text
        formatted = "\n".join([f"- Score {r.get('score')}: {r.get('desc')}" for r in rules])
        return formatted, strategy_name

    # --- Cache Management Logic ---
    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {} # Reset if file is corrupted
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _get_hash(self, text: str) -> str:
        """
        Key: Generate a unique fingerprint
        Hash = MD5( headline + current strategy name )
        This way, if you change the strategy, the Hash will change, triggering a recalculation instead of reading the old strategy's cache!
        """
        raw_string = f"{text}|{self.current_strategy_name}"
        return hashlib.md5(raw_string.encode('utf-8')).hexdigest()

    # --- Execution Logic ---
    def analyze_row(self, headline: str):
        headline = str(headline).strip()
        # 1. Calculate hash with strategy signature
        item_hash = self._get_hash(headline)

        # 2. Check cache
        if item_hash in self.cache:
            # print(f"Cache Hit: {headline[:15]}...")
            return self.cache[item_hash]

        # 3. No cache, call API
        try:
            res = self.chain.invoke({"headline": headline})
            output = {"score": res.score, "reason": res.reasoning}
            
            # Write to cache
            self.cache[item_hash] = output
            return output
            
        except Exception as e:
            print(f"Error: {headline[:15]}... | {e}")
            return {"score": 0.0, "reason": "Error"}

    def run_csv(self, input_csv, output_csv, text_col='title', date_col='date', limit=None):
        print(f"Processing: {input_csv} | Strategy: {self.current_strategy_name}")
        df = pd.read_csv(input_csv)
        if limit: df = df.head(limit)
        
        results = []
        
        for idx, row in df.iterrows():
            res = self.analyze_row(row[text_col])
            
            results.append({
                "timestamp": row[date_col],
                "headline": row[text_col],
                "score": res['score'],
                "reason": res['reason']
            })
            
            # Checkpoint: Save cache every 10 items
            if (idx + 1) % 10 == 0:
                self._save_cache()
                print(f"Processed {idx + 1}/{len(df)}")
                
        self._save_cache() # Save one last time at the end
        
        final_df = pd.DataFrame(results)
        final_df.to_csv(output_csv, index=False)
        print(f"Done! Saved to {output_csv}")

# ==========================================
# testing
# ==========================================
# if __name__ == "__main__":
#     # Standard
#     runner = CryptoSentimentRunner() 
#     runner.run_csv("news_data.csv", "results_standard.csv", limit=5)

#     # non-standard strategy
#     # 哪怕 headline 一样，因为策略名变了，Hash 也会变，会重新触发 API 调用
#     print("\n--- Switching Strategy ---")
#     runner_meme = CryptoSentimentRunner(strategy_name="degen_meme")
#     runner_meme.run_csv("news_data.csv", "results_meme.csv", limit=5)