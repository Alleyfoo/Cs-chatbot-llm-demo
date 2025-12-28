# CS Chatbot LLM

Local-first chatbot playground that reuses the original cleanroom queue to serve multi-turn answers. The project keeps
everything on disk (Excel workbooks + JSONL transcripts) so you can prototype conversational flows without standing up a
cloud broker.

## Overview
- Chat pipeline reuses the existing Excel queue at `data/email_queue.xlsx`.
- `ChatService` wraps the legacy email cleaner so knowledge lookups and guardrails continue to work for conversational turns.
- CLI utilities handle intake (`tools/chat_ingest.py`), processing (`tools/chat_worker.py`), and delivery
  (`tools/chat_dispatcher.py`).
- Streamlit UI (`ui/app.py`) offers a quick inbox/worker/dispatcher experience with a live transcript preview.
- Static HTML (`ui/chat_demo.html`) mirrors the demo by replaying the dispatcher transcript via a "Load Latest Transcript" button.

## Benchmarking
Measure end-to-end worker throughput with the bundled script:
```bash
python tools/benchmark_chat.py --queue data/benchmark_queue.xlsx --reset --repeat 3
```
The script ingests sample messages, drains the queue via `ChatService`, and prints JSON metrics (elapsed seconds, messages processed per second).
Add `--messages-json path/to/messages.json` to benchmark custom workloads or `--dispatch` to log responses via the web-demo adapter.

## Webhook API
Spin up the FastAPI server to emulate a web widget ingest point:
```bash
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```
Then POST chat messages to `/chat/enqueue` to reuse the Excel queue path:
```bash
curl -X POST http://localhost:8000/chat/enqueue \\
     -H 'Content-Type: application/json' \\
     -d '{"conversation_id": "web-visit-1", "text": "Need warranty info", "end_user_handle": "visitor-1"}'
```
Follow up with the worker/dispatcher commands (or the Streamlit UI) to generate and log the response.

## Quickstart
### 1. Environment setup
```bash
python -m venv .venv
. .venv/Scripts/activate        # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
(Optional) start Ollama or llama.cpp if you want model-backed responses; otherwise the deterministic stub keeps tests stable.

### 2. Launch the Streamlit playground
```bash
streamlit run ui/app.py
```
Use the form to add chat messages, then press the worker/dispatcher buttons to generate answers. The transcript preview
lists the bot messages stored in `data/chat_web_transcript.jsonl`.

### 3. CLI workflow
```bash
# Seed conversation history
python tools/chat_ingest.py --queue data/email_queue.xlsx \
    --conversation-id demo-web --end-user-handle demo-user \
    "Hello" "When were you founded?"

# Run a single worker pass
python tools/chat_worker.py --queue data/email_queue.xlsx --processor-id cli-worker

# Log responses to the transcript
python tools/chat_dispatcher.py --queue data/email_queue.xlsx \
    --dispatcher-id cli-dispatcher --adapter web-demo --adapter-target data/chat_web_transcript.jsonl
```
Open `ui/chat_demo.html` in a browser and click **Load Latest Transcript** to replay those responses without Streamlit.

## File map
- `app/chat_service.py` – conversational wrapper around the original pipeline/knowledge stack.
- `tools/chat_ingest.py` – enqueue inline strings or JSON payloads into the Excel queue.
- `tools/chat_worker.py` – claims queued rows, calls `ChatService`, and writes the reply payload.
- `tools/chat_dispatcher.py` – acknowledges `responded` rows and (via `chat_adapter_web.WebDemoAdapter`) logs them to a
  JSONL transcript for demos.
- `ui/app.py` – Streamlit dashboard for enqueue ? worker ? dispatch.
- `ui/chat_demo.html` – static HTML mock with quick answers + transcript loader.

## Knowledge & data sources
Grounding facts still come from the markdown/Excel knowledge templates described in `docs/chat_queue_design.md`.
During development the repo keeps sample data only as locally generated artifacts; `.gitignore` blocks anything under
`data/` except for the `.gitkeep` sentinel.

## Testing
```bash
python -m pytest tests/test_chat_ingest.py tests/test_chat_worker.py tests/test_migrate_queue_chat.py
```
Add additional suites as you extend the chat workflow.

## Documentation
- `docs/chat_queue_design.md` – full schema + processing flow for the chat queue.
- `docs/chat_runbook.md` – operational steps for the webhook, worker, dispatcher loop.
- `docs/chat_migration_plan.md` – phased plan for replacing the email cleaner with the chatbot stack.
- `docs/runbook.md` – legacy email runbook (now annotated with a migration note while the chat playbook is drafted).

## Legacy status
The repository originated as the "Customer Service Email Pre-Cleaner". Email-specific binaries, docs, and tests remain for
historical reference; the active workstream is the chat experience outlined above.
