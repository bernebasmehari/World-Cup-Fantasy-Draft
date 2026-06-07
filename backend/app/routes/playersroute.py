from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.player import Player


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db        # gives the session to the route
    finally:
        db.close()      # closes it automatically when done


@router.get("/players")
def get_players(db: Session = Depends(get_db)):
    return db.query(Player).all()