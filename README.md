# SC6117-Project-LLM-Driven-Crypto-Sentiment-Quantification-Backtesting-Engine

NTU SC6117 project: LLM-Driven Crypto Sentiment Quantification &amp; Backtesting Engine

## Sentiment Engine struct

```
root/
├── .env                        # openAI API key
├── run_sentiment.py            # run sentiment engine -- get sentiment score
├── api_server.py               # fastAPI of python-backend
├── start_server.sh             # start server
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

## how to use api_server.py

change ./.env to use real API keys

#### Start the server directly through a Python file

```python
# default port number is 8000
python api_server.py

# change port number
python api_server.py --port 6432

# start reload (for develop)
python api_server.py --port 6432 --reload
```

#### use shell

```shell
# default port number (8000)
./start_server.sh

# change port number 6432
./start_server.sh -p 6432

# change port number && Host
./start_server.sh --port 9000 --host 127.0.0.1
```


#### use PM2

if want to local test:

do temp change:

cherry-pick ：

get the tmp code for testing

```python
# ./presentation/apps/dashboard/src/lib/api-config.ts
# change API_BASE_URL to make sure that use local service
export const API_BASE_URL = 'http://localhost:6432';

```

ecosystem.config.js add the python-backend

```js
{
            name: "python-backend",
            script: "api_server.py",
            interpreter: "python3", 
            args: "--port 8000",    // port number
            cwd: "../",              // make sure this is the directory where api_server.py is located
            autorestart: true,
            watch: false,         
        }
```

then

```shell
pnpm install

pnpm run build

pm2 start ecosystem.config.js
```
