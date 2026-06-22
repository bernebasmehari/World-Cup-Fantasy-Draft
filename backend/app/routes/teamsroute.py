from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal

from ..database import SessionLocal
from ..models.team import Team
from ..models.user import User
from ..models.draftteam import DraftTeam
from ..scoring import team_points, round_index

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class GroupResult(BaseModel):
    result: Literal["win", "draw", "loss"]
    goals: int = 0

class KnockoutResult(BaseModel):
    round_reached: Literal["round_of_32", "round_of_16", "quarterfinal", "semifinal", "final", "champion"]
    goals: int = 0

class DraftTeamCreate(BaseModel):
    user_id: int
    team_id: int
    pick_number: int
    room_code: str


@router.get("/teams")
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    return [
        {
            "id": t.id, "name": t.name, "group": t.group,
            "group_wins": t.group_wins, "group_draws": t.group_draws, "group_losses": t.group_losses,
            "goals_scored": t.goals_scored, "furthest_round": t.furthest_round,
            "points": team_points(t),
        }
        for t in teams
    ]

# call once per group-stage match a drafted team plays
@router.post("/teams/{team_id}/group-result")
def record_group_result(team_id: int, body: GroupResult, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if body.result == "win":
        team.group_wins += 1
    elif body.result == "draw":
        team.group_draws += 1
    else:
        team.group_losses += 1
    team.goals_scored += body.goals

    db.commit()
    db.refresh(team)
    return {"id": team.id, "name": team.name, "points": team_points(team)}

# call when a drafted team advances in (or wins) the knockout stage
@router.post("/teams/{team_id}/knockout-result")
def record_knockout_result(team_id: int, body: KnockoutResult, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # only move furthest_round forward — protects against a duplicate/out-of-order call
    if round_index(body.round_reached) > round_index(team.furthest_round):
        team.furthest_round = body.round_reached
    team.goals_scored += body.goals

    db.commit()
    db.refresh(team)
    return {"id": team.id, "name": team.name, "points": team_points(team)}


# records a pick — same pattern as before, just pointed at teams. The WebSocket
# draft room can call this on every pick once it's drafting teams instead of players.
@router.post("/draft-teams")
def draft_team(body: DraftTeamCreate, db: Session = Depends(get_db)):
    existing = db.query(DraftTeam).filter_by(team_id=body.team_id, room_code=body.room_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="That team has already been drafted in this room.")

    pick = DraftTeam(user_id=body.user_id, team_id=body.team_id, pick_number=body.pick_number, room_code=body.room_code)
    db.add(pick)
    db.commit()
    db.refresh(pick)
    return pick

@router.get("/draft-teams/{room_code}")
def get_room_picks(room_code: str, db: Session = Depends(get_db)):
    return db.query(DraftTeam).filter(DraftTeam.room_code == room_code).order_by(DraftTeam.pick_number).all()


@router.get("/leaderboard/{room_code}")
def get_leaderboard(room_code: str, db: Session = Depends(get_db)):
    users = db.query(User).filter(User.room_code == room_code).all()
    leaderboard = []
    for user in users:
        picks = db.query(DraftTeam).filter_by(user_id=user.id, room_code=room_code).all()
        roster, total = [], 0.0
        for pick in picks:
            team = db.query(Team).filter(Team.id == pick.team_id).first()
            if team:
                pts = team_points(team)
                total += pts
                roster.append({"team": team.name, "points": pts})
        leaderboard.append({"user": user.name, "total_points": total, "teams": roster})

    leaderboard.sort(key=lambda u: u["total_points"], reverse=True)
    return leaderboard
