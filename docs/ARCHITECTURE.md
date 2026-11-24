# Architecture notes

## Request flow
1. Streamlit sends a question to `POST /chat` with a bearer token.
2. FastAPI validates the demo JWT.
3. `backend.services.route_question` classifies the question as `rag`, `sql`, or `reports`.
4. SQL and report routes query SQLAlchemy models in SQLite.
5. RAG route retrieves indexed chunks from `knowledge_chunks`.
6. The response contains an answer, route name, and (for RAG) source filenames.

## RAG ingestion
Supported formats: PDF, DOCX, TXT, CSV, XLSX and XLS.
Text is extracted, normalized, split into overlapping chunks, embedded, and stored in SQLite with source metadata. Search combines cosine similarity and lexical token overlap. When an OpenAI API key is configured, OpenAI embedding vectors are used; otherwise a local deterministic hashing fallback is used.

## Data model
- customers
- products
- orders
- order_items
- support_tickets
- knowledge_chunks

The included seed script creates synthetic sample data only.
