from app.database import Base
from sqlalchemy import Column, Integer, String
from .user import User
from .team import Team
from sqlalchemy import ForeignKey

class DraftTeam(Base):
    __tablename__ = "draft_teams"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    pick_number = Column(Integer, index=True)
    room_code = Column(String, index=True)
