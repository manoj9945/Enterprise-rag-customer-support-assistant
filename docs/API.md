# API reference

Interactive OpenAPI docs are available at `/docs` when the backend is running.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/login` | Obtain demo JWT |
| POST | `/chat` | Route question to RAG, SQL or reports |
| GET | `/customers` | List sample customers |
| GET | `/orders` | List sample orders |
| GET | `/products` | List sample products |
| GET | `/tickets` | List support tickets |
| GET | `/documents` | List uploaded documents |
| POST | `/documents/upload` | Upload and index a document |
| POST | `/documents/ingest-samples` | Index files in `data/documents` |

Except `/health` and `/auth/login`, endpoints require `Authorization: Bearer <token>`.
