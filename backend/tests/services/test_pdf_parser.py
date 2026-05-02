from app.services.pdf_parser import CHUNK_OVERLAP, CHUNK_SIZE, _split


def test_split_basic():
    text = "a" * 1200
    chunks = _split(text)
    assert all(len(c) <= CHUNK_SIZE for c in chunks)
    # 後続チャンクの先頭は前チャンクの末尾と重複している
    assert chunks[1][: CHUNK_OVERLAP] == chunks[0][CHUNK_SIZE - CHUNK_OVERLAP :]


def test_split_short_text():
    text = "short"
    assert _split(text) == ["short"]


def test_split_empty():
    assert _split("") == []


def test_split_whitespace_only():
    assert _split("   \n  ") == []
