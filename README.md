# CodeAlpha_AIChatbot

Website chatbot for the CodeAlpha Cloud Computing Internship (Task 4). Answers are grounded in documents in `data/knowledge/`.

## Architecture
```
Browser widget (static/widget.js, widget.css)  -- POST /api/chat -->  FastAPI (app/main.py)
   session id in localStorage                                          |- validation + rate limit (per IP)
                                                                       |- retrieval: TF-IDF over data/knowledge/*.md (app/retrieval.py)
                                                                       |- AI: Anthropic Messages API, server-side key (app/llm.py)
                                                                       |- fallback: intent matcher (app/engine.py) / best document passage
                                                                       '- history: SQLite (app/store.py)
```

## How replies are generated
Every reply carries a `mode`, shown as a badge in the chat:
| mode | meaning |
|---|---|
| `ai` | Real LLM call. Prompt = system rules + top-3 retrieved passages + last turns. Told to answer only from context. |
| `retrieval` | No AI. Best-matching passage from the documents, shown verbatim. |
| `rules` | No AI. Predefined reply from `data/intents.json` (greetings, contact, etc). |
| `fallback` | No AI. "Didn't understand" message. |

No API key, or provider error/timeout -> automatic fallback to `retrieval`/`rules`/`fallback`, labelled as no-AI. The UI never presents fallback replies as AI.

## Environment variables
| name | default | purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | empty | Enables AI mode. Server only. |
| `LLM_MODEL` | `claude-sonnet-5-5` | Model name |
| `LLM_MAX_TOKENS` / `LLM_TIMEOUT` | 400 / 20 | Output cap / seconds |
| `LLM_API_URL` | Anthropic messages URL | Override endpoint |
| `RATE_LIMIT` / `RATE_WINDOW` | 20 / 60 | Messages per IP per window (seconds) |
| `ALLOWED_ORIGINS` | empty | Comma list; enable CORS for cross-site embedding |
| `TRUST_PROXY` | 0 | `1` behind a load balancer (uses X-Forwarded-For) |
| `CHAT_DB_PATH` | `./chat.db` | SQLite file |

Copy `.env.example` to `.env` (git-ignored). Never commit keys.

## Run (Windows PowerShell)
```powershell
cd CodeAlpha_AIChatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "your-key"   # optional
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. `GET /api/health` shows `ai_configured`.

## Test
```powershell
python -m pytest -q
```
The LLM provider is mocked in tests; no real AI call is made.

## Add knowledge
Put `.md` files in `data/knowledge/` (use `#` headings; each heading becomes a searchable chunk). Restart.

## Deploy (Docker)
```bash
docker build -t ca-chatbot .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=... -v chatdata:/data ca-chatbot
```
- Render / Railway: new Web Service from the GitHub repo, Docker runtime, set env vars in dashboard, health check path `/api/health`.
- AWS App Runner / Elastic Beanstalk / Cloud Run: push image, set env vars as secrets, port 8000.
- Mount persistent storage at `/data` or history resets on redeploy.

## Embed on another site
```html
<link rel="stylesheet" href="https://YOUR-HOST/static/widget.css">
<script src="https://YOUR-HOST/static/widget.js" data-api="https://YOUR-HOST"></script>
```
Set `ALLOWED_ORIGINS=https://your-site.com` on the server.

## Limitations
- Rate limiter is per process, in memory (use Redis for multiple instances).
- History is keyed by an anonymous session id; anyone with the id can read it. No accounts. Chat text is stored unencrypted in SQLite; users can delete it with the trash button.
- Retrieval is keyword TF-IDF, not embeddings; paraphrased questions can miss.
- Knowledge base covers only facts in the CodeAlpha internship PDF; pricing/refund/hours are not published, so the bot says so.
- AI mode needs a real key; it is covered by mocked tests only.
