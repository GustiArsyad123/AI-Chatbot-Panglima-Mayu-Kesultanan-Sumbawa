import os
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from pathlib import Path

# This module provides simple PDF ingestion and a stubbed retrieval
# For production use you should replace the embedding/store with
# a vector DB (Chroma, FAISS, Pinecone) and real embeddings (OpenAI, sentence-transformers)


def extract_text_from_pdf(path: str) -> List[Dict[str, Any]]:
    """Extracts text per page and returns list of dicts with page and text."""
    reader = PdfReader(path)
    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        docs.append({"page": i + 1, "text": text})
    return docs


def ingest_pdf(path: str, dest_dir: str = "./data") -> Dict[str, Any]:
    p = Path(path)
    assert p.exists(), "PDF not found"
    docs = extract_text_from_pdf(path)
    # Save a simple JSON-lines per doc for manual RAG
    out_dir = Path(dest_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{p.stem}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(str(d) + "\n")
    return {"source": str(p), "pages": len(docs), "stored": str(out_path)}


def simple_retrieve(query: str, source_paths: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
    """A very simple substring-based retriever across ingested JSONL files.
    This is a fallback for when embeddings/vector DBs are not configured.
    """
    results = []
    for sp in source_paths:
        p = Path(sp)
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    # eval used for simplicity; in production use json
                    item = eval(line.strip())
                except Exception:
                    continue
                txt = item.get("text", "")
                if query.lower() in txt.lower():
                    results.append({"source": sp, "page": item.get("page"), "text": txt[:100]})
    return results[:top_k]
