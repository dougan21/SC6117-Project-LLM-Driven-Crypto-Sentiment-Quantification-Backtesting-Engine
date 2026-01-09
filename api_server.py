import argparse
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Literal

import httpx
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage

# try to import pipeline functions
from lib.sentiment_engine import CryptoSentimentRunner, load_dotenv

try:
    from lib.klineAcquision import (get_price_data_last_n_days,
                                    get_price_data_range,
                                    parse_hourly_datetime)
except Exception:
    get_price_data_last_n_days = None
    get_price_data_range = None
    parse_hourly_datetime = None

try:
    from lib.prepare_dataset import prepare_dataset as prepare_dataset_func
except Exception:
    prepare_dataset_func = None

try:
    from lib.sentiment_strategy_backtest import \
        run_backtest as run_backtest_func
except Exception:
    run_backtest_func = None

try:
    from lib.export_backtest_json import \
        export_backtest_json as export_backtest_json_func
except Exception:
    export_backtest_json_func = None
try:
    from lib.export_backtest_json import \
        build_records_from_backtest as build_records_func
except Exception:
    build_records_func = None

# lightweight logger fallback if lib.logger not present
try:
    from lib.logger import LOG, LOG_ERR
except Exception:
    def LOG(msg: str):
        print(msg)

    def LOG_ERR(msg: str):
        print(msg)

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


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[str] = None


class ChatbotRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


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

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5628",
        "http://127.0.0.1:5628",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    raw_history = request.history

    LOG(f"Received frontend message: {user_message}")

    try:
        #  call core analysis logic
        # 'standard_crypto' for default strategy
        runner = get_runner("standard_crypto")

        # LangChain need not timestamp, only role + content
        langchain_history = []
        for msg in raw_history:
            if msg.role == "user":
                langchain_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_history.append(AIMessage(content=msg.content))

        #  runner analyze for chat history
        ai_reply = runner.analyze_for_chat(
            user_input=user_message,
            chat_history=langchain_history
        )

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

            # Explicitly handle rate limiting
            if resp.status_code == 429:
                LOG_ERR(f"[Debug] NewsAPI rate limit exceeded")
                raise HTTPException(
                    status_code=429,
                    detail="News API rate limit exceeded. Please try again later or upgrade your API plan."
                )

            if resp.status_code != 200:
                LOG_ERR(f"[Debug] NewsAPI error content: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
        except HTTPException:
            raise
        except Exception as e:
            LOG_ERR(f"Error fetching news: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    articles = data.get("articles", []) if isinstance(data, dict) else []
    processed_news = []
    for i, art in enumerate(articles[:limit]):
        # Use URL + index to ensure uniqueness, or generate UUID if no URL
        url = art.get("url") or ""
        uid = f"{url}-{i}" if url else uuid.uuid4().hex
        title = art.get("title") or ""
        abstract = art.get("description") or art.get("content") or ""
        pub_time = art.get("publishedAt") or ""
        sentiment_label = "neutral"
        processed_news.append(NewsItem(
            id=uid,
            title=title,
            abstract=abstract,
            timestamp=pub_time,
            sentiment=sentiment_label,
        ))

    LOG("[Debug] All processing completed, preparing to return results")
    return processed_news


# ==========================================
# Pipeline API models + endpoints
# ==========================================


class RunSentimentRequest(BaseModel):
    input_csv: str
    output_csv: str
    strategy: Optional[str] = None
    text_col: str = "SUMMARY"
    date_col: str = "DATETIME"
    limit: Optional[int] = None
    background: bool = False


class GenericResponse(BaseModel):
    status: str
    detail: Optional[str] = None
    path: Optional[str] = None


@app.post("/pipeline/run_sentiment", response_model=GenericResponse)
def api_run_sentiment(req: RunSentimentRequest, background_tasks: BackgroundTasks):
    """Run sentiment quantification on a CSV and write output CSV."""
    try:
        # ensure envs are loaded for OpenAI key
        try:
            load_dotenv()
        except Exception:
            pass

        runner = get_runner(req.strategy or "standard_crypto")

        def _job():
            runner.run_csv(input_csv=req.input_csv,
                           output_csv=req.output_csv,
                           text_col=req.text_col,
                           date_col=req.date_col,
                           limit=req.limit)

        if req.background:
            background_tasks.add_task(_job)
            return GenericResponse(status="started", detail="Background task started", path=req.output_csv)

        _job()
        return GenericResponse(status="ok", detail="Completed", path=req.output_csv)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FetchKlinesRequest(BaseModel):
    symbol: str = "BTC/USDT"
    timeframe: str = "5m"
    days: Optional[int] = None
    start: Optional[str] = None
    end: Optional[str] = None
    out_parquet: str = "./data/kline_output.parquet"
    background: bool = False


@app.post("/pipeline/fetch_klines", response_model=GenericResponse)
def api_fetch_klines(req: FetchKlinesRequest, background_tasks: BackgroundTasks):
    if get_price_data_last_n_days is None and get_price_data_range is None:
        raise HTTPException(
            status_code=500, detail="Kline acquisition functions not available")

    def _job():
        if req.days is not None and get_price_data_last_n_days is not None:
            df = get_price_data_last_n_days(
                symbol=req.symbol, timeframe=req.timeframe, days=req.days)
        else:
            if not req.start or not req.end:
                raise ValueError(
                    "Either 'days' or both 'start' and 'end' must be provided")
            if parse_hourly_datetime is None or get_price_data_range is None:
                raise ValueError(
                    "Range fetch not available in this environment")
            start_ts = parse_hourly_datetime(req.start)
            end_ts = parse_hourly_datetime(req.end)
            df = get_price_data_range(
                symbol=req.symbol, timeframe=req.timeframe, start_time=start_ts, end_time=end_ts)

        Path(req.out_parquet).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(req.out_parquet)

    try:
        if req.background:
            background_tasks.add_task(_job)
            return GenericResponse(status="started", detail="Background fetch started", path=req.out_parquet)
        _job()
        return GenericResponse(status="ok", detail="Saved klines", path=req.out_parquet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PrepareDatasetRequest(BaseModel):
    price_parquet: str
    sentiment_csv: str
    out: str
    decay_span: int = 12
    start: Optional[str] = None
    end: Optional[str] = None
    background: bool = False


@app.post("/pipeline/prepare_dataset", response_model=GenericResponse)
def api_prepare_dataset(req: PrepareDatasetRequest, background_tasks: BackgroundTasks):
    if prepare_dataset_func is None:
        raise HTTPException(
            status_code=500, detail="prepare_dataset function not available")

    def _job():
        start_ts = parse_hourly_datetime(
            req.start) if req.start and parse_hourly_datetime else None
        end_ts = parse_hourly_datetime(
            req.end) if req.end and parse_hourly_datetime else None
        prepare_dataset_func(price_parquet=req.price_parquet, sentiment_csv=req.sentiment_csv,
                             out_path=req.out, decay_span=req.decay_span, start_time=start_ts, end_time=end_ts)

    try:
        if req.background:
            background_tasks.add_task(_job)
            return GenericResponse(status="started", detail="Background prepare started", path=req.out)
        _job()
        return GenericResponse(status="ok", detail="Prepared dataset", path=req.out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RunBacktestRequest(BaseModel):
    input_parquet: str
    price_col: str = "close"
    sentiment_col: str = "sentiment_score"
    output_parquet: Optional[str] = None
    background: bool = False
    # include a minimal subset of strategy params
    window: int = 12
    upper_th: float = 0.2
    lower_th: float = -0.2
    delta_th: float = 0.1
    w_trend: float = 0.7
    w_mom: float = 0.3
    max_strength: float = 0.5
    alpha: float = 0.3
    max_drawdown: float = 0.2


@app.post("/pipeline/run_backtest", response_model=GenericResponse)
def api_run_backtest(req: RunBacktestRequest, background_tasks: BackgroundTasks):
    if run_backtest_func is None:
        raise HTTPException(
            status_code=500, detail="run_backtest not available")

    def _job():
        params = None
        # call function
        run_backtest_func(input_parquet=Path(req.input_parquet), price_col=req.price_col, sentiment_col=req.sentiment_col, output_path=Path(req.output_parquet) if req.output_parquet else None,
                          params=None)

    try:
        if req.background:
            background_tasks.add_task(_job)
            return GenericResponse(status="started", detail="Backtest started", path=req.output_parquet)
        _job()
        return GenericResponse(status="ok", detail="Backtest completed", path=req.output_parquet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ExportBacktestRequest(BaseModel):
    backtest_parquet: str
    price_col: str = "close"
    output_json: str
    initial_capital: float = 100000.0
    time_format: str = "iso"


@app.post("/pipeline/export_backtest", response_model=GenericResponse)
def api_export_backtest(req: ExportBacktestRequest):
    if export_backtest_json_func is None:
        raise HTTPException(
            status_code=500, detail="export_backtest_json not available")
    try:
        export_backtest_json_func(backtest_parquet=Path(req.backtest_parquet), price_col=req.price_col, output_json=Path(
            req.output_json), initial_capital=req.initial_capital, time_format=req.time_format)
        return GenericResponse(status="ok", detail="Exported", path=req.output_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simple endpoint to serve exported backtest JSON to frontend
@app.get("/api/chart-data")
def chart_data(
    backtest_parquet: Optional[str] = Query(
        None, description="optional backtest parquet path to generate data from"),
    cryptoPair: Optional[str] = Query(
        None, description="crypto pair, e.g. BTC/USD"),
    price_col: str = Query("close"),
    initial_capital: float = Query(100000.0),
    points: Optional[int] = Query(
        None, description="downsample to at most this many points"),
    startDateTime: Optional[str] = Query(None),
    endDateTime: Optional[str] = Query(None),
    # legacy aliases accepted by some clients
    start: Optional[str] = Query(
        None, description="legacy alias for startDateTime"),
    end: Optional[str] = Query(
        None, description="legacy alias for endDateTime"),
    time_format: str = Query("iso"),
    background_tasks: BackgroundTasks = None,
):
    LOG(
        f"[Debug] /api/chart-data called with backtest_parquet={backtest_parquet}, startDateTime={startDateTime}, endDateTime={endDateTime}, points={points}")
    # support legacy query aliases `start` and `end` (some clients use these)
    if (not startDateTime) and start:
        startDateTime = start
    if (not endDateTime) and end:
        endDateTime = end

    # Smart downsampling: if points not specified, calculate reasonable default based on time range
    if points is None:
        try:
            if startDateTime and endDateTime:
                s_dt = datetime.fromisoformat(
                    startDateTime.replace("Z", "+00:00"))
                e_dt = datetime.fromisoformat(
                    endDateTime.replace("Z", "+00:00"))
                time_diff = e_dt - s_dt
                days = time_diff.total_seconds() / 86400

                # Calculate reasonable points based on duration:
                # - < 1 day: 500 points (every ~3 minutes for 1-day)
                # - 1-7 days: 1000 points (every ~10 minutes for 1 week)
                # - 7-30 days: 2000 points (every ~20 minutes for 1 month)
                # - > 30 days: 3000 points (every ~45 minutes for 3 months)
                if days < 1:
                    points = 500
                elif days < 7:
                    points = 1000
                elif days < 30:
                    points = 2000
                else:
                    points = 3000
                LOG(
                    f"[Debug] Auto-calculated points={points} for {days:.1f} days of data")
            else:
                # Default if no time range specified
                points = 2000
                LOG(
                    f"[Debug] Using default points={points} (no time range specified)")
        except Exception as e:
            LOG_ERR(f"[Debug] Failed to calculate smart points: {e}")
            points = 2000  # fallback default
    source = None
    chosen_parquet = None
    # If client didn't provide a backtest parquet, try to auto-resolve one from results/
    if not backtest_parquet:
        try:
            candidates = list(Path("results").glob("backtest_*.parquet"))
            chosen = None
            # If user provided start/end, prefer a backtest file whose time range covers the request
            if startDateTime or endDateTime:
                try:
                    s_req = datetime.fromisoformat(startDateTime.replace(
                        "Z", "+00:00")) if startDateTime else None
                except Exception:
                    s_req = None
                try:
                    e_req = datetime.fromisoformat(endDateTime.replace(
                        "Z", "+00:00")) if endDateTime else None
                except Exception:
                    e_req = None

                for p in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
                    try:
                        import pandas as _pd
                        df = _pd.read_parquet(p)
                        idx = df.index if isinstance(
                            df.index, _pd.DatetimeIndex) else None
                        if idx is None:
                            continue
                        tmin, tmax = idx.min(), idx.max()
                        if s_req and e_req:
                            if (tmin <= s_req) and (tmax >= e_req):
                                chosen = p
                                break
                        elif s_req:
                            if tmin <= s_req <= tmax:
                                chosen = p
                                break
                        elif e_req:
                            if tmin <= e_req <= tmax:
                                chosen = p
                                break
                    except Exception:
                        continue

            # If not chosen by time coverage, try month-pattern by startDateTime
            if not chosen and startDateTime:
                try:
                    s = datetime.fromisoformat(
                        startDateTime.replace("Z", "+00:00"))
                    month_pattern = f"backtest_{s.year}-{s.month:02d}*.parquet"
                    month_cands = list(Path("results").glob(month_pattern))
                    if month_cands:
                        chosen = sorted(
                            month_cands, key=lambda p: p.stat().st_mtime, reverse=True)[0]
                except Exception:
                    chosen = None

            # Final fallback: newest backtest_*.parquet
            if not chosen and candidates:
                chosen = sorted(
                    candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]

            if chosen:
                backtest_parquet = str(chosen)
        except Exception:
            backtest_parquet = None
    records = None
    # QUICK PATH: prefer reading from precomputed merged parquet slices under data/merged
    if not backtest_parquet:
        try:
            # parse requested time window (if provided)
            s_req = None
            e_req = None
            if startDateTime:
                s_req = datetime.fromisoformat(startDateTime.replace(
                    "Z", "+00:00")).astimezone(timezone.utc)
            if endDateTime:
                e_req = datetime.fromisoformat(endDateTime.replace(
                    "Z", "+00:00")).astimezone(timezone.utc)

            merged_dir = Path("data/merged")
            merged_files = sorted(merged_dir.glob(
                "*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
            used_files = []
            df_slice = None
            if merged_files:
                import pandas as _pd
                for p in merged_files:
                    try:
                        tmp = _pd.read_parquet(p)
                        tmp.index = _pd.to_datetime(tmp.index, utc=True)
                        # if no window specified, accept this file
                        if s_req is None and e_req is None:
                            used_files.append(p)
                            df_slice = tmp if df_slice is None else _pd.concat(
                                [df_slice, tmp])
                            continue
                        # check overlap
                        if (e_req is not None and tmp.index.max() < s_req) or (s_req is not None and tmp.index.min() > e_req):
                            continue
                        used_files.append(p)
                        df_slice = tmp if df_slice is None else _pd.concat(
                            [df_slice, tmp])
                    except Exception:
                        continue

            if df_slice is not None and len(df_slice):
                df_slice = df_slice.sort_index()
                # determine slice boundaries
                start_bound = s_req or df_slice.index.min()
                end_bound = e_req or df_slice.index.max()
                df_req = df_slice.loc[start_bound:end_bound]
                # if we have rows, decide sync vs async
                if len(df_req) > 0:
                    # persist a small prepared parquet for pipeline functions
                    prepared_path = Path("data/prepared_runtime.parquet")
                    df_req.to_parquet(prepared_path)
                    chosen_parquet = ",".join(
                        [str(x) for x in used_files]) if used_files else str(prepared_path)
                    # if small enough, run synchronously using existing pipeline
                    SYNC_ROW_LIMIT = 3000
                    if len(df_req) <= SYNC_ROW_LIMIT:
                        if run_backtest_func is None or build_records_func is None:
                            return JSONResponse(status_code=202, content={"status": "generated", "detail": "Pipeline functions unavailable for sync processing", "chosen_parquet": chosen_parquet})
                        backtest_runtime = Path(
                            "results/backtest_runtime.parquet")
                        run_backtest_func(input_parquet=prepared_path, price_col=price_col,
                                          sentiment_col="sentiment_score", output_path=backtest_runtime, params=None)
                        records = build_records_func(
                            backtest_runtime, price_col=price_col, initial_capital=initial_capital, time_format=time_format, points=points)
                        source = "merged-sync"
                        chosen_parquet = str(prepared_path)
                    else:
                        # schedule background processing
                        if run_backtest_func is None or build_records_func is None:
                            return JSONResponse(status_code=202, content={"status": "generated", "detail": "Pipeline functions unavailable for async processing", "chosen_parquet": chosen_parquet})
                        job_id = uuid.uuid4().hex
                        backtest_runtime = Path(
                            f"results/backtest_runtime_{job_id}.parquet")
                        ui_json = Path(
                            f"results/backtest_for_ui_runtime_{job_id}.json")

                        def _bg_task(prep: str, out_bt: str, out_json: str):
                            try:
                                run_backtest_func(input_parquet=Path(
                                    prep), price_col=price_col, sentiment_col="sentiment_score", output_path=Path(out_bt), params=None)
                                recs = build_records_func(Path(
                                    out_bt), price_col=price_col, initial_capital=initial_capital, time_format=time_format, points=points)
                                # write ui json
                                with open(out_json, "w", encoding="utf-8") as f:
                                    json.dump(recs, f, ensure_ascii=False)
                            except Exception as e:
                                LOG_ERR(f"Background job {job_id} failed: {e}")

                        # add background task
                        if background_tasks is not None:
                            background_tasks.add_task(_bg_task, str(
                                prepared_path), str(backtest_runtime), str(ui_json))
                            return JSONResponse(status_code=202, content={"status": "queued", "job_id": job_id, "detail": "Processing in background", "output_parquet": str(backtest_runtime), "output_json": str(ui_json), "source": "merged-queued", "chosen_parquet": chosen_parquet})
                        else:
                            return JSONResponse(status_code=202, content={"status": "queued", "detail": "Background processing not available (no BackgroundTasks)"})
        except Exception as e:
            LOG_ERR(f"Quick-path merged handling failed: {e}")

    if backtest_parquet:
        if build_records_func is None:
            raise HTTPException(
                status_code=500, detail="server cannot build records from parquet (function missing)")
        try:
            records = build_records_func(Path(backtest_parquet), price_col=price_col,
                                         initial_capital=initial_capital, time_format=time_format, points=points)
            source = "parquet"
            chosen_parquet = backtest_parquet
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # fallback to a default demo JSON for local development if present
        default_demo = Path("results/backtest_for_ui.json")
        if default_demo.exists():
            try:
                with default_demo.open("r", encoding="utf-8") as f:
                    records = json.load(f)
                    source = "demo"
                    chosen_parquet = str(default_demo)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"failed reading default demo json: {e}")
        else:
            # No backtest_parquet or demo JSON — attempt to use the precomputed sentiment CSV you supplied
            # Priority: the specific file results/sentiment_2025-07-01_to_2025-08-01.csv
            candidate = Path("results/sentiment_2025-07-01_to_2025-08-01.csv")
            if not candidate.exists():
                raise HTTPException(
                    status_code=404, detail="No chart data found. Provide a backtest_parquet or place precomputed CSV at results/sentiment_2025-07-01_to_2025-08-01.csv")
            # Found precomputed sentiment CSV — use it to prepare dataset, run backtest and build records
            sentiment_csv_path = str(candidate)
            price_parquet = Path("data/kline_output.parquet")
            if not price_parquet.exists():
                LOG_ERR(
                    f"Price parquet not found at {price_parquet}; cannot run backtest automatically")
                return JSONResponse(status_code=202, content={
                    "status": "generated",
                    "detail": "Precomputed sentiment CSV found but price parquet missing; please run pipeline.fetch_klines or provide data/kline_output.parquet.",
                    "sentiment_csv": sentiment_csv_path
                })
            if prepare_dataset_func is None or run_backtest_func is None or build_records_func is None:
                LOG_ERR(
                    "One of prepare_dataset/run_backtest/build_records functions is missing; cannot complete pipeline automatically")
                return JSONResponse(status_code=202, content={
                    "status": "generated",
                    "detail": "Precomputed sentiment CSV found but server missing pipeline functions to produce chart data.",
                    "sentiment_csv": sentiment_csv_path
                })
            try:
                start_ts = parse_hourly_datetime(
                    startDateTime) if startDateTime and parse_hourly_datetime else None
                end_ts = parse_hourly_datetime(
                    endDateTime) if endDateTime and parse_hourly_datetime else None
                prepared_parquet = Path("data/prepared_runtime.parquet")
                backtest_parquet = Path("results/backtest_runtime.parquet")

                LOG(
                    f"[Debug] Preparing dataset from price={price_parquet} sentiment={sentiment_csv_path} -> {prepared_parquet}")
                prepare_dataset_func(price_parquet=str(price_parquet), sentiment_csv=str(
                    sentiment_csv_path), out_path=str(prepared_parquet), decay_span=12, start_time=start_ts, end_time=end_ts)

                LOG(
                    f"[Debug] Running backtest on prepared dataset -> {backtest_parquet}")
                run_backtest_func(input_parquet=Path(prepared_parquet), price_col=price_col,
                                  sentiment_col="sentiment_score", output_path=Path(backtest_parquet), params=None)

                LOG(
                    f"[Debug] Building records from backtest parquet {backtest_parquet}")
                records = build_records_func(Path(backtest_parquet), price_col=price_col,
                                             initial_capital=initial_capital, time_format=time_format, points=points)
            except Exception as e:
                LOG_ERR(f"Automatic pipeline failed: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Automatic pipeline failed: {e}")

    # If we have built `records`, optionally filter them to the requested start/end window
    if records and (startDateTime or endDateTime):
        try:
            s_req = datetime.fromisoformat(startDateTime.replace(
                "Z", "+00:00")).astimezone(timezone.utc) if startDateTime else None
        except Exception as ex:
            LOG_ERR(f"Failed to parse startDateTime: {ex}")
            s_req = None
        try:
            e_req = datetime.fromisoformat(endDateTime.replace(
                "Z", "+00:00")).astimezone(timezone.utc) if endDateTime else None
        except Exception as ex:
            LOG_ERR(f"Failed to parse endDateTime: {ex}")
            e_req = None

        def _in_range(rec: dict) -> bool:
            if not rec or not rec.get("time"):
                return False
            try:
                time_str = rec.get("time", "")
                if not time_str:
                    return False
                t = datetime.fromisoformat(time_str.replace(
                    "Z", "+00:00")).astimezone(timezone.utc)
            except Exception:
                return False
            if s_req and t < s_req:
                return False
            if e_req and t > e_req:
                return False
            return True

        # `records` is expected to be a list of dicts; if it's a pandas-like object, convert accordingly
        if isinstance(records, list):
            records = [r for r in records if _in_range(r)]
        else:
            try:
                import pandas as _pd
                if isinstance(records, _pd.DataFrame):
                    df_rec = records.copy()
                    if 'time' not in df_rec.columns:
                        LOG_ERR("DataFrame records missing 'time' column")
                    else:
                        df_rec['time'] = _pd.to_datetime(
                            df_rec['time'], utc=True)
                        if s_req is not None:
                            df_rec = df_rec[df_rec['time'] >= s_req]
                        if e_req is not None:
                            df_rec = df_rec[df_rec['time'] <= e_req]
                        records = df_rec.to_dict(orient='records')
            except Exception as ex:
                LOG_ERR(f"Failed to filter DataFrame records: {ex}")
                # if conversion fails, leave records as-is
                pass

    # Normalize records so that the values at startDateTime become the baseline
    # If a startDateTime was provided, find the first record at or after that timestamp
    # and scale subsequent `holdValue` and `strategyValue` so that the baseline maps
    # to `initial_capital` (preserves currency scale but anchors at requested start).
    if records and startDateTime:
        try:
            s_req = datetime.fromisoformat(startDateTime.replace(
                "Z", "+00:00")).astimezone(timezone.utc)
        except Exception as ex:
            LOG_ERR(f"Failed to parse startDateTime for normalization: {ex}")
            s_req = None

        if s_req is not None and isinstance(records, list) and len(records) > 0:
            # find first index with time >= s_req
            baseline_idx = None
            for idx, rec in enumerate(records):
                if not rec or not rec.get("time"):
                    continue
                try:
                    time_str = rec.get("time", "")
                    if not time_str:
                        continue
                    t = datetime.fromisoformat(time_str.replace(
                        "Z", "+00:00")).astimezone(timezone.utc)
                except Exception:
                    continue
                if t >= s_req:
                    baseline_idx = idx
                    break

            if baseline_idx is not None:
                base_rec = records[baseline_idx]
                try:
                    base_hold = float(base_rec.get("holdValue") or 0.0)
                except Exception:
                    base_hold = 0.0
                try:
                    base_strat = float(base_rec.get("strategyValue") or 0.0)
                except Exception:
                    base_strat = 0.0

                # Only normalize if baseline values are non-zero
                if base_hold != 0.0 or base_strat != 0.0:
                    for j in range(baseline_idx, len(records)):
                        rec = records[j]
                        if not rec:
                            continue
                        try:
                            hv = float(rec.get("holdValue") or 0.0)
                            if base_hold and base_hold != 0.0:
                                rec["holdValue"] = float(
                                    hv / base_hold * float(initial_capital))
                        except Exception as ex:
                            LOG_ERR(
                                f"Failed to normalize holdValue at index {j}: {ex}")
                            pass
                        try:
                            sv = float(rec.get("strategyValue") or 0.0)
                            if base_strat and base_strat != 0.0:
                                rec["strategyValue"] = float(
                                    sv / base_strat * float(initial_capital))
                        except Exception as ex:
                            LOG_ERR(
                                f"Failed to normalize strategyValue at index {j}: {ex}")
                            pass

    try:
        payload = {
            "source": source or "unknown",
            "chosen_parquet": chosen_parquet,
            "records": records or []
        }
        return JSONResponse(payload)
    except Exception as e:
        LOG_ERR(f"Failed to build response payload: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to build chart data response: {str(e)}")


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
