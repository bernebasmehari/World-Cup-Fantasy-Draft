from .models.team import Team

GROUP_WIN_POINTS = 3
GROUP_DRAW_POINTS = 1
GOALS_MULTIPLIER = 0.5

# Total points for the FURTHEST round reached — not stacked. See note above.
ROUND_ORDER = [
    "group_stage", "round_of_32", "round_of_16",
    "quarterfinal", "semifinal", "final", "champion",
]
KNOCKOUT_POINTS = {
    "group_stage": 0, "round_of_32": 2, "round_of_16": 4,
    "quarterfinal": 6, "semifinal": 8, "final": 10, "champion": 15,
}

def group_stage_points(team: Team) -> float:
    return (team.group_wins * GROUP_WIN_POINTS) + (team.group_draws * GROUP_DRAW_POINTS)

def knockout_points(team: Team) -> float:
    return KNOCKOUT_POINTS.get(team.furthest_round, 0)

def goal_points(team: Team) -> float:
    return team.goals_scored * GOALS_MULTIPLIER

def team_points(team: Team) -> float:
    return group_stage_points(team) + knockout_points(team) + goal_points(team)

def round_index(round_name: str) -> int:
    """Used to stop furthest_round from accidentally moving backwards."""
    return ROUND_ORDER.index(round_name) if round_name in ROUND_ORDER else -1
