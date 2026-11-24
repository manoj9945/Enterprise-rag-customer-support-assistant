import os, shutil
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import Base, engine, get_db
from .models import Customer, Product, Order, SupportTicket
from .seed import seed_database
from .security import create_access_token, verify_password, hash_password, decode_token
from .services import handle_question
from .rag import ingest_file, ingest_directory

Base.metadata.create_all(bind=engine)
seed_database()
app = FastAPI(title="Enterprise RAG Customer Support API", version="1.0.0",
              description="Integrated RAG, SQL operations and analytics demo API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8501","http://127.0.0.1:8501"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    question: str

def current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    payload = decode_token(authorization.split(" ",1)[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@app.get("/health")
def health():
    return {"status":"ok", "service":"enterprise-rag-assistant"}

@app.post("/auth/login")
def login(body: LoginRequest):
    # Demo credentials; replace with a persisted user store before real deployment.
    if body.username == "admin" and body.password == os.getenv("DEMO_ADMIN_PASSWORD", "admin123"):
        return {"access_token": create_access_token(body.username), "token_type":"bearer"}
    raise HTTPException(status_code=401, detail="Incorrect username or password")

@app.post("/chat")
def chat(body: ChatRequest, db: Session = Depends(get_db), user=Depends(current_user)):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return handle_question(question, db)

@app.get("/customers")
def customers(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.scalars(select(Customer).order_by(Customer.id)).all()
    return [{"id":x.id,"name":x.name,"email":x.email,"city":x.city} for x in rows]

@app.get("/orders")
def orders(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.scalars(select(Order).order_by(Order.order_date.desc()).limit(100)).all()
    return [{"id":x.id,"customer_id":x.customer_id,"status":x.status,"total_amount":x.total_amount,
             "payment_status":x.payment_status,"tracking_number":x.tracking_number} for x in rows]

@app.get("/products")
def products(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.scalars(select(Product).order_by(Product.id)).all()
    return [{"id":x.id,"name":x.name,"category":x.category,"price":x.price,"stock":x.stock} for x in rows]

@app.get("/tickets")
def tickets(db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.scalars(select(SupportTicket).order_by(SupportTicket.id.desc())).all()
    return [{"id":x.id,"customer_id":x.customer_id,"subject":x.subject,"status":x.status,"priority":x.priority} for x in rows]

@app.post("/documents/ingest-samples")
def ingest_samples(user=Depends(current_user)):
    return {"results": ingest_directory()}

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), user=Depends(current_user)):
    allowed = {".pdf",".docx",".txt",".csv",".xlsx",".xls"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Supported formats: PDF, DOCX, TXT, CSV, XLSX")
    folder = Path("data/documents")
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    destination = folder / safe_name
    with destination.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    try:
        count = ingest_file(destination)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"filename":safe_name, "chunks_indexed":count}

@app.get("/documents")
def documents(user=Depends(current_user)):
    folder = Path("data/documents")
    folder.mkdir(parents=True, exist_ok=True)
    return {"documents":[p.name for p in folder.iterdir() if p.is_file()]}

@app.on_event("startup")
def startup():
    ingest_directory()
