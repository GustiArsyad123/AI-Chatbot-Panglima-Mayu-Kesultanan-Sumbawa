import os
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from auth import get_password_hash, verify_password, create_access_token, decode_access_token
from rag import ingest_pdf, simple_retrieve
from rag_langchain import create_vectorstore_from_pdf, query_collection
from auth import oauth2_scheme, decode_access_token
from fastapi.security import OAuth2PasswordBearer
from fastapi import Header
from pydantic import BaseModel
import shutil

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Panglima Mayu Chatbot - Backend")


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = None


@app.post("/signup")
def signup(u: UserCreate):
    db = SessionLocal()
    existing = db.query(User).filter(User.username == u.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username exists")
    user = User(username=u.username, full_name=u.full_name, hashed_password=get_password_hash(u.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "created", "username": user.username}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/create_test_user")
def create_test_user():
    """Utility endpoint to create a test user `testuser` with password `testpass`.
    Not for production — useful for quick local testing.
    """
    db = SessionLocal()
    existing = db.query(User).filter(User.username == "testuser").first()
    if existing:
        return {"msg": "exists"}
    user = User(username="testuser", full_name="Test User", hashed_password=get_password_hash("testpass"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "created", "username": user.username, "password": "testpass"}


def get_current_username(token: str = Depends(lambda: None)):
    # For simple testing we accept token via query param or header bearer
    # FastAPI dependencies can be improved with OAuth2PasswordBearer
    return None


def get_current_user(token: str = Depends(oauth2_scheme)):
    # decode token and return username if valid; raise 401 otherwise
    td = decode_access_token(token)
    if td is None or td.username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    db = SessionLocal()
    user = db.query(User).filter(User.username == td.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.post("/ingest_pdf")
def api_ingest_pdf(file: UploadFile = File(...)):
    uploads = "./uploads"
    os.makedirs(uploads, exist_ok=True)
    dest = os.path.join(uploads, file.filename)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    res = ingest_pdf(dest, dest_dir="./data")
    return res


@app.post("/ingest_pdf_langchain")
def api_ingest_pdf_langchain(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    uploads = "./uploads"
    os.makedirs(uploads, exist_ok=True)
    dest = os.path.join(uploads, file.filename)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    res = create_vectorstore_from_pdf(dest, persist_dir="./chroma_db")
    return res


class ChatRequest(BaseModel):
    query: str
    sources: list = None


@app.post("/chat")
def chat(req: ChatRequest):
    # Rudimentary pipeline: use simple_retrieve across stored JSONL files
    if not req.sources:
        # find all ingested files
        import glob
        req.sources = glob.glob("./data/*.jsonl")
    hits = simple_retrieve(req.query, req.sources)
    # Compose a minimal reply: include hits as citations
    if not hits:
        answer = "Maaf, tidak ditemukan referensi langsung dalam dokumen yang terindeks."
    else:
        answer = "Ditemukan referensi pada halaman: " + ", ".join([f\"{h['page']} ({h['source']})\" for h in hits])
    return {"answer": answer, "sources": hits}


class LangChainChatRequest(BaseModel):
    query: str
    collection_name: str = None
    k: int = 3
    mode: str = "Umum"


@app.post("/chat_langchain")
def chat_langchain(req: LangChainChatRequest, current_user: User = Depends(get_current_user)):
    # Require a collection name (defaults to first collection if not provided)
    persist_dir = "./chroma_db"
    collection = req.collection_name
    if not collection:
        # try to pick a collection from the persist dir
        try:
            collections = os.listdir(persist_dir)
            if collections:
                collection = collections[0]
        except Exception:
            collection = None
    if not collection:
        raise HTTPException(status_code=400, detail="No collection specified and none found in chroma_db")

    try:
        res = query_collection(req.query, collection_name=collection, persist_dir=persist_dir, k=req.k, user_mode=req.mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return res
