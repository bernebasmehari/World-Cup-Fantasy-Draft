from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.user import User
from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    room_code: str

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db        # gives the session to the route
    finally:
        db.close()      # closes it automatically when done


#route to create a new user in the database
@router.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(name=user.name, room_code=user.room_code)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

#route to get all users in the database
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()