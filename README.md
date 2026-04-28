# CS Chatbot LLM

A demo customer-service chatbot that runs on your own machine. It shows how an AI assistant can answer customer questions reliably, handle multiple conversations at once, and stay safe to deploy in a real business.

## What this project does

Imagine the chat box on a company's support page. When a visitor types a question, something has to:

1. **Receive the message** without losing it, even if hundreds arrive at once.
2. **Look up the right answer** from the company's own knowledge (FAQs, policies, product info).
3. **Reply** in the customer's language, and remember earlier messages in the same conversation.
4. **Hand off to a human** when the AI isn't confident enough to answer.

This project is a working example of all four steps, built so it can run on a laptop for demos but designed the way a production system would be.

## Why it matters

Most chatbot demos break the moment two people use them at the same time, or they "hallucinate" answers they can't back up. This demo addresses both problems:

- **Safe under load.** Incoming messages go into a small local database (SQLite, a file-based database that needs no server) instead of a shared spreadsheet. That means several worker processes can handle messages in parallel without overwriting each other's work.
- **Grounded answers.** The bot only replies using approved company knowledge files, so it doesn't invent facts.
- **Portable.** The whole stack runs locally with one command, so reviewers can try it without cloud accounts or paid services.

## How the pieces fit together

- **A web endpoint (API)** receives chat messages and drops them into the queue. (An "API" here just means a URL the website's chat widget can post to.)
- **A queue** holds pending messages in a single SQLite file. Workers pick messages up one at a time.
- **One or more workers** read messages off the queue, ask the language model for a reply, and save the answer along with the conversation history.
- **A local language model** (Ollama, an app for running open-source AI models on your own computer) generates the actual replies. No data leaves the machine.
- **A simple UI** (Streamlit, a tool for building quick web dashboards in Python) lets you watch messages flow through the system live.

Everything is bundled with Docker Compose (a tool that starts several connected services with one command), so you can launch the API, the workers, and the AI model together.

## Highlights for reviewers

- **Multi-worker safe.** Workers claim messages atomically, so the same message is never answered twice.
- **API-key protected ingest.** The endpoint that accepts new messages requires a secret key by default.
- **Scales horizontally.** You can run more workers with a single flag (`--scale worker=3`) to handle more traffic.
- **Load-tested.** A Locust script (Locust is a tool that simulates many users at once) is included so you can measure throughput.
- **Backwards compatible.** The older Excel-based version still works if you set `USE_DB_QUEUE=false`, but the database path is now the default.

## Try it yourself

### Option A: One-command demo with Docker

If you have Docker installed, this is the easiest path:

```bash
docker compose up --build
# Run more workers in parallel:
docker compose up --build --scale worker=3
```

### Option B: Run it directly with Python

**1. Set up a Python environment** (a "virtual environment" is just a sandbox so this project's libraries don't interfere with anything else on your computer):

```bash
python -m venv .venv
. .venv/Scripts/activate        # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# set an ingest API key for the server
setx INGEST_API_KEY dev-api-key
```

**2. Start the web server** that accepts incoming chat messages:

```bash
export INGEST_API_KEY=dev-api-key   # set your own secret in real deployments
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

**3. Send a sample message** (this is what a website's chat widget would do):

```bash
curl -X POST http://localhost:8000/chat/enqueue \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: ${INGEST_API_KEY}" \
     -d '{"conversation_id": "web-visit-1", "text": "Need warranty info", "end_user_handle": "visitor-1"}'
```

**4. Start a worker** to pick up the message and reply:

```bash
USE_DB_QUEUE=true python tools/chat_worker.py --processor-id cli-worker --watch
```

### Option C: Try it from the command line, end to end

```bash
# Drop two messages into the queue
USE_DB_QUEUE=true python tools/chat_ingest.py --conversation-id demo-web "Hello" "When were you founded?"

# Run a worker that watches for new messages and answers them
USE_DB_QUEUE=true python tools/chat_worker.py --processor-id cli-worker --watch
```

For a visual demo, open the Streamlit dashboard (`ui/app.py`) or the static HTML mock-up (`ui/chat_demo.html`).

### Stress-testing it

If you want to see how the system behaves under heavy traffic, install Locust and point it at the running server:

```bash
pip install locust
INGEST_API_KEY=dev-api-key locust -f load_tests/locustfile.py --host http://localhost:8000
```

## Where to look in the code

- `app/chat_service.py` — the conversational layer that turns a single question into a grounded answer.
- `app/queue_db.py` — defines the queue and conversation-history tables in SQLite.
- `tools/chat_ingest.py` — adds new messages to the queue (from the command line or a JSON file).
- `tools/chat_worker.py` — the worker loop: claims a message, generates a reply, saves it.
- `tools/chat_dispatcher.py` — marks finished replies as delivered and writes a transcript for demos.
- `ui/app.py` — Streamlit dashboard showing the queue, workers, and dispatch in one view.
- `ui/chat_demo.html` — a lightweight HTML chat demo that loads the transcript.

## A note on the data

The bot only answers using approved company knowledge — markdown and Excel templates described in `docs/chat_queue_design.md`. Sample data is generated locally; the repository does not ship customer data or transcripts. (`.gitignore` blocks anything under `data/` so nothing sensitive is ever committed by accident.)
