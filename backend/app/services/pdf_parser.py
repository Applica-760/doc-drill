import io

from pypdf import PdfReader

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def extract_chunks(pdf_bytes: bytes) -> list[str]:
    """PDFバイト列をテキストチャンク列に変換する。"""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    full_text = "\n".join(
        page.extract_text() or "" for page in reader.pages
    ).strip()
    return _split(full_text)


def _split(text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c.strip()]
