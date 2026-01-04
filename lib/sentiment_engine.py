import pandas as pd
import json
import os
import hashlib
import asyncio
from dotenv import load_dotenv
from typing import Dict, Optional, List
from tqdm import tqdm
import threading

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
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
                 model: str = "gpt-4o-mini",
                 concurrency: int = 1): # <--- default 1 (serial)
                #  model: str = "Qwen/Qwen2.5-7B-Instruct"):
        
        self.config_file = config_file
        self.cache_file = cache_file
        self.concurrency = concurrency
        self.model_name = model
        
        # 1. Load strategy rules
        # self.current_strategy_name is used to generate cache Hash to distinguish different strategies
        self.rules_text, self.current_strategy_name = self._load_strategy_rules(
            strategy_name)

        # 2. Load local cache (result cache)
        self.cache = self._load_cache()
        # Lock to protect cache from concurrent modification (json.dump iterates dict)
        self.cache_lock = threading.RLock()

        # 3. Initialize LangChain components
        self.parser = PydanticOutputParser(pydantic_object=SentimentResult)
        self.llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)

        # Initialize a slightly more creative LLM for Chat (temperature 0.3-0.7 is better for chat)
        self.chat_llm = ChatOpenAI(model=model, temperature=0.3, api_key=api_key)

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
        formatted = "\n".join(
            [f"- Score {r.get('score')}: {r.get('desc')}" for r in rules])
        return formatted, strategy_name

    # --- Cache Management Logic ---
    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}  # Reset if file is corrupted
        return {}

    def _save_cache(self):
        # Dump a shallow copy while holding the lock to avoid "dictionary changed size during iteration"
        with self.cache_lock:
            cache_copy = dict(self.cache)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_copy, f, ensure_ascii=False, indent=2)

    def _get_hash(self, text: str) -> str:
        """
        Key: Generate a unique fingerprint
        Hash = MD5( headline + current strategy name )
        This way, if you change the strategy, the Hash will change, triggering a recalculation instead of reading the old strategy's cache!
        """
        raw_string = f"{text}|{self.current_strategy_name}"
        return hashlib.md5(raw_string.encode('utf-8')).hexdigest()
    
    # =========================================================================
    # Chatbot Backend Logic
    # =========================================================================
    def analyze_for_chat(self, user_input: str, chat_history: List[BaseMessage] = []) -> str:
        """
        Enhanced Chat Analysis Function
        Features:
        1. Does not enforce JSON format, outputs natural language.
        2. Equipped with common sense reasoning (enhanced through System Prompt).
        3. Supports conversation history (Context).
        """
        
        # define System Prompt
        system_text = f"""
        You are a senior Crypto Market Analyst.
        Your task is to analyze user-provided news or statements and determine whether they are [Bullish] or [Bearish] for the cryptocurrency market, providing in-depth reasoning.
        
        Core Requirements:
        1. **Apply Common Sense & Background Knowledge**: User input may be very brief (e.g., "Trump died"). You must identify entities (e.g., Trump = former U.S. President/candidate) and analyze their relationship with the crypto market based on their political stance.
        2. **Analysis Dimensions**: Think from multiple perspectives including macroeconomics, regulatory policies, and market sentiment.
        3. **Current Strategy Reference**: While you should analyze flexibly, please refer to the current quantitative strategy preferences:
           {self.rules_text}
        
        Output Format Requirements:
        - First, clearly state the conclusion: [Bullish], [Bearish], or [Neutral].
        - Then explain the reasoning in simple and understandable language.
        """

        # Construct message list (Prompt Construction)
        messages = [
            SystemMessage(content=system_text),
            *chat_history, # Unpack history
            HumanMessage(content=user_input)
        ]

        # 3. Call LLM (No Pydantic parsing, directly get content)
        # No caching here because the conversation context is different each time
        try:
            response = self.chat_llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error during analysis: {str(e)}"

    # --- Execution Logic ---
    def analyze_row(self, headline: str):
        headline = str(headline).strip()
        # 1. Calculate hash with strategy signature
        item_hash = self._get_hash(headline)

        # 2. Check cache
        with self.cache_lock:
            cached = self.cache.get(item_hash)
        if cached is not None:
            return cached

        # 3. No cache, call API
        try:
            res = self.chain.invoke({"headline": headline})
            output = {"score": res.score, "reason": res.reasoning}

            # Write to cache under lock
            with self.cache_lock:
                self.cache[item_hash] = output
            return output

        except Exception as e:
            print(f"Error: {headline[:15]}... | {e}")
            return {"score": 0.0, "reason": "Error"}
        
    # --- Asynchronous Method (Parallel Processing of Single Row) ---
    async def analyze_row_async(self, headline: str, semaphore: asyncio.Semaphore):
        """
        Asynchronous unit: Check cache -> (Semaphore control -> API request) -> Return result
        Note: Only returns data here, does not perform file writing to avoid IO conflicts
        """
        headline = str(headline).strip()
        item_hash = self._get_hash(headline)

        # Check cache (memory operation, no await needed)
        if item_hash in self.cache:
            return {**self.cache[item_hash], "headline": headline, "cached": True}

        # Call API (concurrency limited by semaphore)
        async with semaphore:
            try:
                # use ainvoke instead of invoke
                res = await self.chain.ainvoke({"headline": headline})
                output = {"score": res.score, "reason": res.reasoning}
                # Return result with hash for subsequent cache update
                return {**output, "headline": headline, "hash": item_hash, "cached": False}
            except Exception as e:
                # Simple error handling to prevent a single failure from blocking the entire batch
                return {"score": 0.0, "reason": f"Error: {str(e)}", "headline": headline, "hash": item_hash, "cached": False}

    # --- Asynchronous Batch Processing Core Logic ---
    async def _process_batch_async(self, df, text_col):
        semaphore = asyncio.Semaphore(self.concurrency)
        tasks = []
        
        print(f"Starting Async Loop with Concurrency={self.concurrency}...")
        
        # Create tasks
        for _, row in df.iterrows():
            task = self.analyze_row_async(row[text_col], semaphore)
            tasks.append(task)
        
        # Execute concurrently and display progress bar
        # Results order is consistent with tasks order
        results = []
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Async Processing"):
            result = await f
            results.append(result)
            
        return results

    def run_csv(self, input_csv, output_csv, text_col='title', date_col='date', limit=None):
        print(
            f"Processing: {input_csv} | Strategy: {self.current_strategy_name}")
        df = pd.read_csv(input_csv)
        if limit:
            df = df.head(limit)

        results = []

        # asyn or sync based on concurrency setting
        if self.concurrency > 1:
            # ---------------------------
            # Asynchronous Parallel (Async)
            # ---------------------------
            print(f"Mode: PARALLEL (Concurrency: {self.concurrency})")

            # run the async batch processor
            raw_results = asyncio.run(self._process_batch_async(df, text_col))
            
            # Post-processing: update cache + organize results
            # Note: asyncio.as_completed returns results in random order, if you need to maintain CSV order,
            # here is a simple handling, or you can use df merge to align
            cache_updates = 0
            
            for res in raw_results:
                # Update in-memory cache
                if not res.get("cached", True) and "hash" in res:
                    self.cache[res['hash']] = {"score": res['score'], "reason": res['reason']}
                    cache_updates += 1
                
                # We iterate over the original df and find the corresponding result in raw_results
                match = next((item for item in raw_results if item["headline"] == res["headline"]), None)
            
            # Rebuild ordered DataFrame
            # build a map for quick lookup
            result_map = {r["headline"]: r for r in raw_results}
            
            for _, row in df.iterrows():
                headline = row[text_col]
                data = result_map.get(headline, {"score": 0, "reason": "Error/Missing"})
                results.append({
                    "timestamp": row[date_col],
                    "headline": headline,
                    "score": data['score'],
                    "reason": data.get('reason', '')
                })

            if cache_updates > 0:
                print(f"Saving {cache_updates} new items to cache...")
                self._save_cache()
        
        else:
            # ---------------------------
            # Synchronous Serial (Sync)
            # ---------------------------
            print(f"Mode: SERIAL (Concurrency: 1)")

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
