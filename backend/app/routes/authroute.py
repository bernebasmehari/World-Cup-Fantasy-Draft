from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from ..models.account import Account

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AuthForm(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(body: AuthForm, db: Session = Depends(get_db)):
    if db.query(Account).filter_by(username=body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken.")
    account = Account(username=body.username, password=body.password)
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"id": account.id, "username": account.username}

@router.post("/login")
def login(body: AuthForm, db: Session = Depends(get_db)):
    account = db.query(Account).filter_by(username=body.username).first()
    if not account or account.password != body.password:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"id": account.id, "username": account.username}
