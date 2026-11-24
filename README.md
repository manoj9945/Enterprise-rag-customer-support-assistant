# Enterprise AI Customer Support & E-Commerce Assistant

An integrated learning/demo application combining:
- Document RAG for policies, FAQs and product information
- SQL-backed customer, order, product, inventory and ticket lookups
- Business snapshot reporting
- FastAPI backend and Streamlit frontend
- JWT-based demo login
- PDF, DOCX, TXT, CSV and Excel document ingestion

## Important scope and honesty notes

This is a functional learning/demo foundation, not a production enterprise platform. The included data is synthetic. The default login is `admin` / `admin123`; change it before any shared deployment. The demo JWT secret must also be changed. RBAC is represented by a demo admin token and should be expanded into a real user/role store before production.

The local no-key RAG fallback uses a deterministic hashed-token vector and lexical matching. This makes the demo usable without a paid API key, but it is not equivalent to a neural embedding model. Set an OpenAI API key in `.env` to use OpenAI embeddings and generated answers. API usage may incur charges.

Python 3.14 compatibility depends on the available wheels for each third-party package. If installation fails, use the error output to adjust package versions or install Python 3.12 side-by-side. Docker is optional for this local version.

## Requirements

- Windows 10/11
- Python 3.14 (the project will attempt this environment first)
- Internet for first-time package installation
- Optional OpenAI API key for neural embeddings and LLM answers

## Quick start (Windows)

1. Extract the ZIP to a folder you can write to.
2. Open PowerShell in the extracted `Enterprise_RAG_Assistant` folder.
3. Run:

   ```powershell
   .\run_project.bat
   ```

4. Wait for both terminal windows to start.
5. Open `http://localhost:8501`.
6. Sign in with `admin` / `admin123`.

The first run creates `.venv`, installs dependencies, creates the SQLite database and seeds sample records.

## Manual start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn backend.main:app --reload
```

In a second PowerShell window:

```powershell
cd path\to\Enterprise_RAG_Assistant
.\.venv\Scripts\Activate.ps1
streamlit run frontend\app.py
```

API docs: `http://127.0.0.1:8000/docs`
Frontend: `http://localhost:8501`

## Configure OpenAI (optional)

Open `.env` and set:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Restart the API after changing `.env`. Do not commit `.env` or share your API key.

## Example questions

- `Where is order 3?`
- `Show customers`
- `Show current inventory`
- `Show monthly sales revenue`
- `What is your return policy?`
- `How long do refunds take?`
- `How do I report a damaged item?`

## Project layout

```text
backend/       FastAPI routes, database models, routing, RAG and security
frontend/      Streamlit application
data/documents Sample policies, FAQ and product data
tests/         Basic unit tests
requirements.txt
.env.example
run_project.bat
```

## Current implementation boundaries

- The query router uses transparent Python rules, not a general autonomous agent.
- The reports module currently returns a basic operational snapshot; monthly time-series reporting is a natural next enhancement.
- Retrieval combines semantic-vector similarity (OpenAI embeddings when configured, local hashed-vector fallback otherwise) and lexical overlap. It includes chunking, source metadata and score-based reranking, but does not yet implement a full parent-child index, neural cross-encoder reranker, or RAGAS benchmark suite.
- Conversational memory is maintained in the Streamlit session display; persistent multi-turn memory is not implemented.
- Authentication uses a demo admin account. Production requires a real user store, stronger RBAC, rate limiting, audit logs and secret management.
- Uploads are stored locally under `data/documents`. Review access controls and file limits before deployment.

## Run tests

```powershell
pytest -q
```

## Troubleshooting

- If `python` points to the wrong installation, check `python --version` and `where.exe python`.
- If a package fails to install on Python 3.14, copy the complete error. We may need a compatible package version or Python 3.12.
- If the UI says it cannot connect, check that the backend terminal is running and visit `/health`.
- If port 8000 or 8501 is busy, stop the other process or change the port.
