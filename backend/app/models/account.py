from app.database import Base
from sqlalchemy import Column, Integer, String

class Account(Base):
    __tablename__ = "accounts"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
