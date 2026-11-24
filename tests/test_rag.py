from backend.rag import split_text

def test_split_text_returns_chunks():
    text = "This is a sentence. " * 200
    chunks = split_text(text, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    assert all(chunks)
    assert all(len(chunk) <= 220 for chunk in chunks)
