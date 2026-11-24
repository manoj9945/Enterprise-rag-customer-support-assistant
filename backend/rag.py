
import os
import re
import json
import math
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

from sqlalchemy import select, delete

from .db import SessionLocal
from .models import KnowledgeChunk


# --------------------------------------------------
# OLLAMA CONFIGURATION
# --------------------------------------------------

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434"
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b"
)


# --------------------------------------------------
# TEXT PROCESSING
# --------------------------------------------------

STOPWORDS = {
    "what", "is", "the", "a", "an", "and", "or",
    "of", "to", "in", "on", "for", "from", "with",
    "how", "when", "where", "why", "who", "which",
    "can", "could", "would", "should", "do", "does",
    "did", "i", "me", "my", "about", "tell", "please",
    "it", "this", "that", "are", "was", "were",
    "will", "be", "am", "you", "your"
}


def split_text(text: str, chunk_size: int = 850, overlap: int = 120):
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(len(text), start + chunk_size)

        if end < len(text):
            boundary = text.rfind(" ", start, end)

            if boundary > start + chunk_size * 0.6:
                end = boundary

        chunks.append(text[start:end].strip())

        if end >= len(text):
            break

        start = max(start + 1, end - overlap)

    return chunks


def _tokens(text):
    words = re.findall(r"[a-z0-9]+", text.lower())

    return [
        word for word in words
        if word not in STOPWORDS and len(word) > 1
    ]


# --------------------------------------------------
# LOCAL EMBEDDINGS
# --------------------------------------------------

def _local_embedding(text, dimensions=256):
    # Stable hashing: SHA-256 produces consistent values
    # across Python restarts.

    vector = [0.0] * dimensions

    for token in _tokens(text):
        digest = hashlib.sha256(
            token.encode("utf-8")
        ).digest()

        idx = int.from_bytes(
            digest[:4],
            byteorder="big"
        ) % dimensions

        vector[idx] += 1.0

    norm = math.sqrt(
        sum(x * x for x in vector)
    ) or 1.0

    return [x / norm for x in vector]


def _embed(texts):
    # Keep the existing optional OpenAI embedding support.
    # If no API key is configured, use local hashing embeddings.

    key = os.getenv("OPENAI_API_KEY", "").strip()

    if key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=key)

            model = os.getenv(
                "OPENAI_EMBEDDING_MODEL",
                "text-embedding-3-small"
            )

            result = client.embeddings.create(
                model=model,
                input=texts
            )

            return [
                item.embedding
                for item in result.data
            ]

        except Exception as exc:
            print(
                f"Embedding API unavailable; "
                f"using local fallback: {exc}"
            )

    return [
        _local_embedding(text)
        for text in texts
    ]


# --------------------------------------------------
# DOCUMENT EXTRACTION
# --------------------------------------------------

def extract_text(path: Path):
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    if suffix == ".pdf":
        from pypdf import PdfReader

        return "\n".join(
            page.extract_text() or ""
            for page in PdfReader(str(path)).pages
        )

    if suffix == ".docx":
        from docx import Document

        return "\n".join(
            p.text
            for p in Document(str(path)).paragraphs
        )

    if suffix == ".csv":
        import pandas as pd

        return pd.read_csv(path).to_string(
            index=False
        )

    if suffix in (".xlsx", ".xls"):
        import pandas as pd

        return pd.read_excel(path).to_string(
            index=False
        )

    raise ValueError(
        f"Unsupported file type: {suffix}"
    )


# --------------------------------------------------
# DOCUMENT INGESTION
# --------------------------------------------------

def ingest_file(path: Path):
    text = extract_text(path)

    chunks = split_text(text)

    vectors = _embed(chunks) if chunks else []

    db = SessionLocal()

    try:
        db.execute(
            delete(KnowledgeChunk).where(
                KnowledgeChunk.document_name == path.name
            )
        )

        for i, (chunk, vector) in enumerate(
            zip(chunks, vectors)
        ):
            db.add(
                KnowledgeChunk(
                    document_name=path.name,
                    chunk_index=i,
                    content=chunk,
                    metadata_json=json.dumps({
                        "source": path.name
                    }),
                    embedding_json=json.dumps(vector)
                )
            )

        db.commit()

    finally:
        db.close()

    return len(chunks)


def ingest_directory(directory="data/documents"):
    folder = Path(directory)

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    results = {}

    for path in folder.iterdir():
        if (
            path.is_file()
            and path.suffix.lower() in {
                ".txt", ".pdf", ".docx",
                ".csv", ".xlsx", ".xls"
            }
        ):
            try:
                results[path.name] = ingest_file(path)

            except Exception as exc:
                results[path.name] = f"ERROR: {exc}"

    return results


# --------------------------------------------------
# SIMILARITY CALCULATION
# --------------------------------------------------

def _cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0

    numerator = sum(
        x * y for x, y in zip(a, b)
    )

    denominator = (
        math.sqrt(sum(x * x for x in a))
        *
        math.sqrt(sum(y * y for y in b))
    )

    return numerator / (denominator or 1)


# --------------------------------------------------
# DOCUMENT RETRIEVAL
# --------------------------------------------------

def retrieve(question: str, top_k: int = 3):
    # Remove uninformative words.
    qtokens = set(_tokens(question))

    if not qtokens:
        return []

    db = SessionLocal()

    try:
        rows = db.scalars(
            select(KnowledgeChunk)
        ).all()

        if not rows:
            return []

        qvec = _embed([question])[0]

        scored = []

        for row in rows:
            dtokens = set(
                _tokens(row.content)
            )

            # Keyword overlap.
            overlap = len(
                qtokens & dtokens
            )

            lexical = overlap / max(
                1, len(qtokens)
            )

            # Skip chunks with insufficient keyword relevance.
            if lexical < 0.25:
                continue

            # Semantic similarity.
            vec = json.loads(
                row.embedding_json or "[]"
            )

            semantic = _cosine(
                qvec,
                vec
            )

            # Combined retrieval score.
            score = (
                0.65 * semantic
                + 0.35 * lexical
            )

            if score < 0.15:
                continue

            scored.append({
                "source": row.document_name,
                "chunk": row.chunk_index,
                "content": row.content,
                "score": round(score, 4)
            })

        return sorted(
            scored,
            key=lambda x: x["score"],
            reverse=True
        )[:top_k]

    finally:
        db.close()


# --------------------------------------------------
# OLLAMA ANSWER GENERATION
# --------------------------------------------------

def generate_with_ollama(question: str, context: str):
    url = f"{OLLAMA_BASE_URL}/api/chat"

    system_prompt = """
You are an e-commerce customer support assistant.

Your task is to answer the user's question using ONLY
the knowledge context supplied to you.

Follow these rules strictly:

1. Use only information present in the supplied context.
2. Do not use outside knowledge.
3. Do not invent policies, dates, prices, names or facts.
4. If the context does not contain the answer, clearly
   say that the information is not available in the
   knowledge documents.
5. Give a simple, direct and helpful answer.
6. Mention the source filename when possible.
7. If the context contains conflicting information,
   do not guess. Explain that the documents differ.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Knowledge context:\n{context}"
                )
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=180
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        answer = (
            result.get("message", {})
            .get("content", "")
            .strip()
        )

        if not answer:
            raise ValueError(
                "Ollama returned an empty answer."
            )

        return answer

    except urllib.error.HTTPError as exc:
        error_details = exc.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            f"Ollama HTTP error {exc.code}: {error_details}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure the Ollama application is running "
            "and the API is available at "
            f"{OLLAMA_BASE_URL}. Details: {exc}"
        ) from exc


# --------------------------------------------------
# RAG ANSWER GENERATION
# --------------------------------------------------

def answer_from_rag(question: str):
    hits = retrieve(question)

    # No relevant documents found.
    if not hits:
        return {
            "answer": (
                "I don't have enough relevant information "
                "in my knowledge documents to answer that "
                "question. Please try asking about company "
                "policies, shipping, returns or products."
            ),
            "sources": []
        }

    # Send the two best matching chunks to Ollama.
    context = "\n\n".join(
        f"[{h['source']}]\n{h['content']}"
        for h in hits[:2]
    )

    try:
        answer = generate_with_ollama(
            question,
            context
        )

    except Exception as exc:
        print(
            f"Ollama answer generation failed: {exc}"
        )

        answer = (
            "I found relevant information in the "
            "knowledge documents, but Ollama could not "
            "generate an answer right now.\n\n"
            "Please check whether Ollama is running "
            "and the configured model is available.\n\n"
            "Retrieved information:\n\n"
            + context[:2000]
        )

    return {
        "answer": answer,
        "sources": [
            {
                "source": h["source"],
                "score": h["score"]
            }
            for h in hits[:2]
        ]
    }
