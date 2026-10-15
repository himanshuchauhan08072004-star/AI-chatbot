# CodeAlpha_AIChatbot

Retrieval-based AI chatbot for websites. CodeAlpha Cloud Computing Internship, Task 4.

## How it works
- `data/intents.json`: predefined input patterns + responses (13 intents, easy to extend for any business).
- `app/engine.py`: TF-IDF (word + character n-grams) + cosine similarity. Below 0.30 confidence returns a fallback reply.
- `app/main.py`: FastAPI. `POST /api/chat`, `GET /api/health`, serves demo site.
- `static/widget.js` + `widget.css`: drop-in chat bubble for any website.
- `tests/`: held-out accuracy test (>= 85%) + API tests.

## Run (Windows PowerShell)
```powershell
cd CodeAlpha_AIChatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000

## Test
```powershell
python -m pytest -q -s
```

## Embed on any website
```html
<link rel="stylesheet" href="https://YOUR-HOST/static/widget.css">
<script src="https://YOUR-HOST/static/widget.js" data-api="https://YOUR-HOST"></script>
```

## Deploy
Docker image included (`docker build -t ca-chatbot .`). Works on Render, AWS App Runner, Elastic Beanstalk, Google Cloud Run.

## Customize
Edit `data/intents.json`: add `tag`, `patterns`, `responses`. Restart server.
