from app.database import Base
from sqlalchemy import Column, Integer, String

class Player(Base):
    __tablename__ = "players"
    # your columns here
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    team =Column(String, index=True)
    position = Column(String, index=True)
    points = Column(Integer, default=0)
