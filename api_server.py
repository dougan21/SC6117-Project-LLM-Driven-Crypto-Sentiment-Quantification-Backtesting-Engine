from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uvicorn
import httpx
import uuid
import os
import argparse
import uvicorn

from lib.sentiment_engine import CryptoSentimentRunner
from lib.logger import LOG, LOG_ERR

# ==========================================
# init Data Models
# ==========================================


class NewsRequest(BaseModel):
    headline: str
    strategy: Optional[str] = "standard_crypto"


class AnalysisResponse(BaseModel):
    headline: str
    score: float
    reason: str
    strategy_used: str


class ChatbotRequest(BaseModel):
    message: str


class ChatbotResponse(BaseModel):
    message: str
    timestamp: str


class NewsItem(BaseModel):
    id: str
    title: str
    abstract: str
    timestamp: str
    sentiment: str  # "positive", "negative", "neutral"


# ==========================================
# init App & engine
# ==========================================
app = FastAPI(
    title="Crypto Sentiment API",
    description="LLM-Driven Crypto Sentiment Quantification Engine API",
    version="1.0"
)

# pre loading (avoid reinitializing on every request)
# Using a global dictionary to cache Runners for different strategies
runners = {}


def get_runner(strategy_name: str):
    if strategy_name not in runners:
        # init new runner
        runners[strategy_name] = CryptoSentimentRunner(
            strategy_name=strategy_name)
    return runners[strategy_name]

# ==========================================
# interfaces
# ==========================================


@app.get("/")
def health_check():
    return {"status": "running", "service": "Sentiment Engine"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_news(request: NewsRequest):
    """
    receive news headline, return sentiment score
    """
    try:
        # 1. get corresponding strategy runner
        runner = get_runner(request.strategy)

        # 2. call core logic (sync method can run in FastAPI, but consider making analyze_row async later)
        result = runner.analyze_row(request.headline)

        # 3. return result (FastAPI will auto convert to JSON)
        return AnalysisResponse(
            headline=request.headline,
            score=result['score'],
            reason=result['reason'],
            strategy_used=request.strategy
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chatbot", response_model=ChatbotResponse)
async def chatbot_endpoint(request: ChatbotRequest):
    """
    chatbot interface for frontend integration
    """
    user_message = request.message
    LOG(f"Received frontend message: {user_message}")

    try:
        #  call core analysis logic
        # 'standard_crypto' for default strategy
        runner = get_runner("standard_crypto")
        result = runner.analyze_row(user_message)

        score = result['score']
        reason = result['reason']

        # map score to natural language trend
        if score >= 0.6:
            trend_str = "Strong Bullish"
            advice = "market shows strong positive sentiment, consider buying opportunities."
        elif score >= 0.2:
            trend_str = "Bullish"
            advice = "market shows positive sentiment, short-term price may rise."
        elif score <= -0.6:
            trend_str = "Strong Bearish"
            advice = "market shows extreme fear, exercise caution."
        elif score <= -0.2:
            trend_str = "Bearish"
            advice = "market shows negative sentiment, consider caution."
        else:
            trend_str = "Neutral / Market Noise"
            advice = "market impact is limited, consider observing."

        # reply construction
        ai_reply = f"""
{trend_str}

AI sentiment analysis:
{reason}

Action advice: {advice}
        """.strip()

    except Exception as e:
        LOG_ERR(f"Error: {e}")
        ai_reply = "Sorry, I am currently unable to analyze this news. Please try again later or check the input content."

    utc_time = datetime.now(timezone.utc)

    # return to Express -> Next.js
    return ChatbotResponse(
        message=ai_reply,
        timestamp=utc_time.isoformat()
    )


@app.get("/api/news", response_model=List[NewsItem])
async def fetch_news_and_analyze(
    # FastAPI get query parameters
    limit: int = Query(
        5, ge=1, le=20, description="the number of news items to fetch (1-20)"),
    query: str = Query("cryptocurrency", description="search keyword")
):
    """
    [GET] from News API get real news, and use LLM engine for sentiment scoring
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        LOG_ERR("[Debug] Error: NEWS_API_KEY not found")
        raise HTTPException(
            status_code=500, detail="Server missing NEWS_API_KEY")
    LOG(f"[Debug] Got NewsAPI Key (length: {len(api_key)})")

    # Asynchronous request to News API
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,           # directly use function parameter query
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,    # directly use function parameter limit
        "apiKey": api_key
    }
    LOG(f"[Debug] Requesting NewsAPI: {url}")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            LOG(f"[Debug] NewsAPI response status code: {resp.status_code}")

            # If NewsAPI returns an error, print the specific reason
            if resp.status_code != 200:
                LOG_ERR(f"[Debug] NewsAPI error content: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            LOG_ERR(f"NewsAPI Error: {e}")
            raise HTTPException(
                status_code=502, detail="Failed to fetch news from external provider")

    articles = data.get("articles", [])
    LOG(f"[Debug] Successfully fetched {len(articles)} news articles")
    processed_news = []

    # Get sentiment analysis engine
    LOG("[Debug] Getting Sentiment Runner...")
    runner = get_runner("standard_crypto")

    # Iterate through news and score (logic remains unchanged)
    for idx, article in enumerate(articles):
        title = article.get("title", "No Title")
        LOG(f"[Debug] Analyzing article {idx+1}: {title[:30]}...")
        description = article.get("description") or "No description available."
        abstract = description[:200] + \
            "..." if len(description) > 200 else description

        # Concatenate content to feed to LLM
        text_to_analyze = f"{title}. {description}"

        try:
            # Call quantification engine
            analysis_result = runner.analyze_row(text_to_analyze)
            score = analysis_result['score']

            # Map score to label
            if score >= 0.2:
                sentiment_label = "positive"
            elif score <= -0.2:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"

        except Exception as e:
            LOG_ERR(f"Analysis Failed for {title}: {e}")
            score = 0.0
            sentiment_label = "neutral"

        # Construct return
        pub_time = article.get("publishedAt") or datetime.now(
            timezone.utc).isoformat()
        unique_id = f"news-{idx}-{uuid.uuid4().hex[:8]}"

        processed_news.append(NewsItem(
            id=unique_id,
            title=title,
            abstract=abstract,
            timestamp=pub_time,
            sentiment=sentiment_label
        ))

    LOG("[Debug] All processing completed, preparing to return results")
    return processed_news

# ==========================================
# start entry point
# ==========================================
if __name__ == "__main__":

    # define command-line arguments
    parser = argparse.ArgumentParser(
        description="Start the Crypto Sentiment API Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to run the server on"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (Dev mode)"
    )

    # parse arguments
    args = parser.parse_args()

    # start Uvicorn
    print(f"Server running on http://{args.host}:{args.port}")
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
