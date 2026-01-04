import os
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter


def create_vectorstore_from_pdf(pdf_path: str, persist_dir: str = "./chroma_db", collection_name: str = None) -> Dict[str, Any]:
    """Ingest PDF pages into a Chroma collection using OpenAI embeddings.

    Saves the collection into `persist_dir` under the given `collection_name`.
    """
    reader = PdfReader(pdf_path)
    texts = []
    metadatas = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        texts.append(text)
        metadatas.append({"source": os.path.basename(pdf_path), "page": i + 1})

    # Split long pages to smaller chunks for better retrieval
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = []
    metas = []
    for t, m in zip(texts, metadatas):
        if not t.strip():
            continue
        chunks = splitter.split_text(t)
        for c in chunks:
            docs.append(c)
            metas.append(m)

    if not docs:
        return {"error": "no_text_extracted"}

    embeddings = OpenAIEmbeddings()
    if collection_name is None:
        collection_name = os.path.splitext(os.path.basename(pdf_path))[0]
    os.makedirs(persist_dir, exist_ok=True)

    vect = Chroma.from_texts(docs, embeddings, metadatas=metas, persist_directory=persist_dir, collection_name=collection_name)
    try:
        vect.persist()
    except Exception:
        # some Chroma versions persist automatically
        pass

    return {"collection_name": collection_name, "persist_directory": persist_dir, "n_chunks": len(docs)}


def query_collection(query: str, collection_name: str, persist_dir: str = "./chroma_db", k: int = 3, user_mode: str = "Umum") -> Dict[str, Any]:
    """Query a Chroma collection and synthesize an answer using OpenAI LLM.

    Returns answer text and the list of source metadata used as citations.
    """
    if not collection_name:
        raise ValueError("collection_name required")

    embeddings = OpenAIEmbeddings()
    vect = Chroma(persist_directory=persist_dir, collection_name=collection_name, embedding_function=embeddings)

    # similarity_search_with_score returns list[(Document, score)]
    hits = vect.similarity_search_with_score(query, k=k)
    context_parts = []
    sources = []
    for doc, score in hits:
        content = getattr(doc, "page_content", str(doc))
        meta = getattr(doc, "metadata", {}) or {}
        src = meta.get("source")
        page = meta.get("page")
        context_parts.append(f"[{src} p.{page}] {content}")
        sources.append({"source": src, "page": page, "score": float(score)})

    context_text = "\n\n".join(context_parts)

    prompt = (
        f"Anda adalah asisten sejarah yang membantu menjawab pertanyaan tentang Panglima Mayu dan konteks Kesultanan Sumbawa. "
        f"Gunakan hanya informasi yang ada di konteks berikut dan selalu sertakan sitasi halaman (format: NamaDokumen p.<halaman>) di akhir jawaban. "
        f"Jika klaim hanya berasal dari sumber komunitas, beri label 'versi tradisi/komunitas'. Mode pengguna: {user_mode}.\n\n"
        f"Konteks:\n{context_text}\n\nPertanyaan: {query}\n\nJawaban (Bahasa Indonesia):"
    )

    llm = OpenAI(temperature=0)
    try:
        answer = llm(prompt)
    except Exception as e:
        answer = f"LLM error: {e}"

    return {"answer": answer, "sources": sources}
