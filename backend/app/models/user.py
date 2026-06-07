from app.database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "user"
    # your columns here
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    room_code = Column(String, index=True)
    draft_order  = Column(Integer, nullable=True)
    
