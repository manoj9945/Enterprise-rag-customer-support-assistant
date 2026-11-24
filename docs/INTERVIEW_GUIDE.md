# Interview explanation guide

## 60-second project summary
"I built an AI-powered e-commerce customer support assistant that combines document-based RAG with structured SQL lookups and operational reporting. A FastAPI backend receives questions and routes them to the appropriate capability. For policy questions, documents are extracted, chunked, embedded and indexed; relevant chunks are retrieved and passed to an LLM with source context. For order and inventory questions, SQLAlchemy queries the relational database. A Streamlit interface exposes chat, customer, order, inventory, ticket and knowledge-base screens."

## Be precise about what is implemented
- Implemented: document extraction for listed formats, chunking, SQLite chunk storage, hybrid lexical/vector scoring, source filenames, SQL lookups, basic reporting, FastAPI endpoints and Streamlit screens.
- Optional: OpenAI embeddings and generated answers when an API key is configured.
- Demo fallback: hashed token vectors and retrieved-context display without an API key.
- Not yet production-grade: multi-user identity management, advanced RBAC, persistent conversational memory, autonomous planning, cross-encoder reranking, complete RAGAS evaluation, distributed vector database and production monitoring.

## Suggested demo sequence
1. Sign in.
2. Ask "What is your return policy?" and show cited document source.
3. Ask "Where is order 3?" and show SQL-backed result.
4. Ask "Show monthly sales revenue" and show report route/business snapshot.
5. Upload a policy document and query it.
