from app.database import Base
from sqlalchemy import Column, Integer, String

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)   # e.g. "Brazil"
    group = Column(String, nullable=True)            # e.g. "A" — optional

    # --- group stage record (drives the 3 / 1 / 0 points) ---
    group_wins = Column(Integer, default=0)
    group_draws = Column(Integer, default=0)
    group_losses = Column(Integer, default=0)

    # --- goals scored across the WHOLE tournament — 0.5 pt each, group + knockout ---
    goals_scored = Column(Integer, default=0)

    # --- furthest knockout stage reached ---
    # one of: "group_stage", "round_of_32", "round_of_16", "quarterfinal",
    #         "semifinal", "final", "champion"
    furthest_round = Column(String, default="group_stage")
