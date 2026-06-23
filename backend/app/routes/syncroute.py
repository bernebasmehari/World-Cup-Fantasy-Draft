"""
POST /sync-standings  — pulls live data from the FIFA API and updates
every team's group-stage record + knockout progression in one shot.
Idempotent: sets values directly rather than incrementing.
"""
import unicodedata, re, requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.team import Team
from ..scoring import round_index

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── FIFA API endpoints (2026 WC) ────────────────────────────────────────────

SEASON  = "285023"
COMP    = "17"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept":     "application/json",
    "Referer":    "https://www.fifa.com/",
}

GROUP_STANDINGS_URL = (
    f"https://api.fifa.com/api/v3/calendar/{COMP}/{SEASON}/289273/standing"
    "?language=en&count=200"
)

# stage_id → our furthest_round key (for teams that WIN through this stage)
KNOCKOUT_STAGES = [
    ("289287", "round_of_32"),
    ("289288", "round_of_16"),
    ("289289", "quarterfinal"),
    ("289290", "semifinal"),
    # Final: winner → champion, loser → final
]
FINAL_STAGE_ID = "289292"

# ── name normalization ───────────────────────────────────────────────────────

# FIFA API name → our database name (for known mismatches)
FIFA_NAME_OVERRIDES: dict[str, str] = {
    "united states":                  "United States",
    "usa":                            "United States",
    "republic of korea":              "South Korea",
    "korea republic":                 "South Korea",
    "ir iran":                        "Iran",
    "china pr":                       "China",
    "cote d ivoire":                  "Ivory Coast",
    "côte d'ivoire":                  "Ivory Coast",
    "democratic republic of congo":   "DR Congo",
    "dr congo":                       "DR Congo",
    "curacao":                        "Curaçao",
    "czechia":                        "Czech Republic",
}

def _norm(name: str) -> str:
    """Lowercase, strip accents, keep alphanumeric + spaces."""
    nfd = unicodedata.normalize("NFD", name)
    stripped = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", "", stripped.lower()).strip()


def _find_team(name_raw: str, db: Session) -> Team | None:
    norm = _norm(name_raw)
    # Check override table first
    canonical = FIFA_NAME_OVERRIDES.get(norm)
    if canonical:
        t = db.query(Team).filter(Team.name == canonical).first()
        if t:
            return t
    # Try exact match (case-insensitive)
    t = db.query(Team).filter(Team.name.ilike(name_raw)).first()
    if t:
        return t
    # Fuzzy: match on normalized form
    for team in db.query(Team).all():
        if _norm(team.name) == norm:
            return team
    return None


# ── fetch helpers ────────────────────────────────────────────────────────────

def _fetch_json(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def _fetch_knockout_matches(stage_id: str) -> list[dict]:
    url = (
        f"https://api.fifa.com/api/v3/calendar/matches"
        f"?idCompetition={COMP}&idSeason={SEASON}&idStage={stage_id}"
        "&language=en&count=200"
    )
    try:
        data = _fetch_json(url)
        return data.get("Results", [])
    except Exception:
        return []


# ── main endpoint ────────────────────────────────────────────────────────────

@router.post("/sync-standings")
def sync_standings(db: Session = Depends(get_db)):
    updated, skipped = [], []

    # ── 1. Group stage standings ─────────────────────────────────────────────
    try:
        standings_data = _fetch_json(GROUP_STANDINGS_URL)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FIFA API error: {e}")

    for row in standings_data.get("Results", []):
        fifa_name = row["Team"]["Name"][0]["Description"]
        team = _find_team(fifa_name, db)

        if not team:
            skipped.append(fifa_name)
            continue

        team.group_wins   = row["Won"]
        team.group_draws  = row["Drawn"]
        team.group_losses = row["Lost"]

        group_goals = row["For"]   # goals scored in group stage only; we store all goals here
        team.goals_scored = group_goals  # will add knockout goals below

        updated.append(team.name)

    db.flush()

    # ── 2. Knockout stage progression + goals ────────────────────────────────

    # Build a map: team_id → (goals_in_knockout, furthest_round_reached)
    # We work through rounds in order; later rounds overwrite earlier ones.
    team_knockout: dict[str, dict] = {}   # fifa_team_id → {goals, round}

    for stage_id, round_key in KNOCKOUT_STAGES:
        matches = _fetch_knockout_matches(stage_id)
        for m in matches:
            # Result codes: 0=not played, 4=home win, 3=away win, 1/2=draw (shouldn't happen in KO)
            result = m.get("Result", 0)
            home_id = m.get("HomeTeamId", "")
            away_id = m.get("AwayTeamId", "")
            home_goals = m.get("HomeTeamScore") or 0
            away_goals = m.get("AwayTeamScore") or 0

            if result == 0:
                continue  # not played yet

            # Both teams participated — loser's furthest round is this stage
            # Winner advances (will be overwritten by a later stage below)
            for tid, goals in [(home_id, home_goals), (away_id, away_goals)]:
                if tid not in team_knockout:
                    team_knockout[tid] = {"goals": 0, "round": "group_stage"}
                team_knockout[tid]["goals"] += goals
                # Mark at least this round; the actual winner check overwrites
                if round_index(round_key) > round_index(team_knockout[tid]["round"]):
                    team_knockout[tid]["round"] = round_key

    # Final: distinguish champion vs finalist
    final_matches = _fetch_knockout_matches(FINAL_STAGE_ID)
    for m in final_matches:
        result = m.get("Result", 0)
        if result == 0:
            continue
        home_id, away_id = m.get("HomeTeamId", ""), m.get("AwayTeamId", "")
        home_g,  away_g  = m.get("HomeTeamScore") or 0, m.get("AwayTeamScore") or 0
        for tid, goals in [(home_id, home_g), (away_id, away_g)]:
            if tid not in team_knockout:
                team_knockout[tid] = {"goals": 0, "round": "group_stage"}
            team_knockout[tid]["goals"] += goals

        winner_id = home_id if result == 4 else away_id
        loser_id  = away_id if result == 4 else home_id
        if winner_id in team_knockout:
            team_knockout[winner_id]["round"] = "champion"
        if loser_id in team_knockout:
            team_knockout[loser_id]["round"] = "final"

    # Apply knockout data — match by FIFA team ID via the standings team list
    team_id_to_db: dict[str, Team] = {}
    for row in standings_data.get("Results", []):
        fifa_id   = row["Team"]["IdTeam"]
        fifa_name = row["Team"]["Name"][0]["Description"]
        team = _find_team(fifa_name, db)
        if team:
            team_id_to_db[fifa_id] = team

    for fifa_id, kdata in team_knockout.items():
        team = team_id_to_db.get(fifa_id)
        if not team:
            continue
        team.goals_scored += kdata["goals"]   # add knockout goals on top of group goals
        if round_index(kdata["round"]) > round_index(team.furthest_round):
            team.furthest_round = kdata["round"]

    db.commit()

    return {
        "status":  "ok",
        "updated": len(updated),
        "skipped": skipped,
        "teams":   updated,
    }
