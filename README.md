# AI-Chatbot-Panglima-Mayu-Kesultanan-Sumbawa

Project scaffold: Backend (FastAPI) + Frontend (Next.js) untuk Chatbot "Panglima Mayu Kesultanan Sumbawa".

Quick-start

- Backend (recommended inside a Python venv):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# copy .env.example to .env and fill SECRET_KEY, OPENAI_API_KEY if available
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Frontend:

```bash
cd frontend
npm install
npm run dev
```

What I added (initial):

- Backend: `main.py`, `auth.py`, `models.py`, `rag.py`, `.env.example`, `requirements.txt`.
- Frontend: minimal Next.js app with `index.js` (login) and `chat.js` (chat UI).

Notes & next steps

- The backend contains a simple PDF ingest + substring retriever (in `rag.py`) as a safe fallback if embeddings/vector DB are not configured. For production-grade RAG, plug in a vector DB (Chroma/FAISS/Pinecone) and embeddings (OpenAI, sentence-transformers) and update `rag.py` accordingly.
- The API currently uses a minimal auth flow. You should replace the token dependency with `OAuth2PasswordBearer` and secure endpoints properly.
- You can now upload PDFs via `/ingest_pdf` (multipart form upload) and ask queries to `/chat`.

If you want, saya bisa:

- (A) Tambah integrasi LangChain + OpenAI embeddings dan contoh ingest+index. (lihat endpoint baru di backend)
- (B) Tambahkan Dockerfile/docker-compose untuk menjalankan seluruh stack.
- (C) Buatkan skema metadata, prompt sistem, format sitasi, dan 20 contoh pertanyaan (requested in your spec).

LangChain + OpenAI (RAG) — quick example

Prereqs: set `OPENAI_API_KEY` in `backend/.env`.

1. Ingest a PDF into Chroma (LangChain)

```bash
curl -X POST "http://localhost:8000/ingest_pdf_langchain" \
	-H "Content-Type: multipart/form-data" \
	-F "file=@/path/to/your/manuscript.pdf"
```

Response contains `collection_name` and number of chunks.

2. Query the collection

```bash
curl -X POST "http://localhost:8000/chat_langchain" \
	-H "Content-Type: application/json" \
	-d '{"query":"Siapa Panglima Mayu dan perannya?","collection_name":"manuscript","k":3, "mode":"Umum"}'
```

The response will include an `answer` (synthesized by OpenAI using retrieved passages) and a `sources` array with `{source, page, score}` entries for citation.

Security & notes

- Current LangChain endpoints assume `OPENAI_API_KEY` is available and will create a local Chroma DB under `./chroma_db`.
- For production: secure endpoints with OAuth2 / JWT, enable rate limits, and validate uploaded files.

Konsep Chatbot Khusus “Panglima Mayu Kesultanan Sumbawa”
