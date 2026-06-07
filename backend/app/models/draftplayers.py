from app.database import Base
from sqlalchemy import Column, Integer, String
from .user import User
from .player import Player
from sqlalchemy import ForeignKey



class DraftPlayer(Base):
    __tablename__ = "draft_players"
    # your columns here
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    pick_number = Column(Integer, index=True)
    room_code = Column(String, index=True)
    