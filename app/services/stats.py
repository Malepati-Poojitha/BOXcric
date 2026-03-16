from sqlalchemy.orm import Session
from app.models.ball import Ball
from app.models.innings import Innings
from app.models.match import Match, MatchStatus
from app.models.player import Player
from app.schemas.score import PlayerCareerStats


def get_player_career_stats(db: Session, player_id: int) -> PlayerCareerStats:
    """Calculate comprehensive career stats for a player."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise ValueError("Player not found")

    # Get all completed matches where this player batted or bowled
    all_balls = db.query(Ball).filter(
        (Ball.batter_id == player_id) | (Ball.bowler_id == player_id)
    ).all()

    innings_ids = set(b.innings_id for b in all_balls)
    match_ids = set()
    for iid in innings_ids:
        inn = db.query(Innings).filter(Innings.id == iid).first()
        if inn:
            match_ids.add(inn.match_id)

    # ---- Batting ----
    batting_balls = [b for b in all_balls if b.batter_id == player_id]
    innings_batted_ids = set(b.innings_id for b in batting_balls)

    # Per-innings runs
    innings_runs: dict[int, int] = {}
    for b in batting_balls:
        innings_runs.setdefault(b.innings_id, 0)
        innings_runs[b.innings_id] += b.runs_scored

    total_runs = sum(innings_runs.values())
    highest_score = max(innings_runs.values()) if innings_runs else 0

    # Not-outs: innings where the player was not dismissed
    dismissed_innings = set(
        b.innings_id for b in all_balls
        if b.dismissed_player_id == player_id
    )
    not_outs = len(innings_batted_ids) - len(dismissed_innings)

    innings_batted = len(innings_batted_ids)
    dismissals = innings_batted - not_outs
    batting_average = round(total_runs / dismissals, 2) if dismissals > 0 else float(total_runs)

    legal_bat_balls = sum(1 for b in batting_balls if b.is_legal)
    strike_rate = round((total_runs / legal_bat_balls) * 100, 2) if legal_bat_balls > 0 else 0.0

    fours = sum(1 for b in batting_balls if b.runs_scored == 4)
    sixes = sum(1 for b in batting_balls if b.runs_scored == 6)

    fifties = sum(1 for r in innings_runs.values() if 50 <= r < 100)
    hundreds = sum(1 for r in innings_runs.values() if r >= 100)

    # ---- Bowling ----
    bowling_balls = [b for b in all_balls if b.bowler_id == player_id]
    innings_bowled_ids = set(b.innings_id for b in bowling_balls)
    innings_bowled = len(innings_bowled_ids)

    legal_bowl_balls = sum(1 for b in bowling_balls if b.is_legal)
    runs_conceded = sum(b.runs_scored + b.extra_runs for b in bowling_balls)
    total_wickets = sum(1 for b in bowling_balls if b.is_wicket)

    bowling_average = round(runs_conceded / total_wickets, 2) if total_wickets > 0 else 0.0
    economy = round((runs_conceded / legal_bowl_balls) * 6, 2) if legal_bowl_balls > 0 else 0.0

    # Best bowling: wickets/runs per innings
    best_wkt, best_runs = 0, 999
    for iid in innings_bowled_ids:
        inn_balls = [b for b in bowling_balls if b.innings_id == iid]
        w = sum(1 for b in inn_balls if b.is_wicket)
        r = sum(b.runs_scored + b.extra_runs for b in inn_balls)
        if w > best_wkt or (w == best_wkt and r < best_runs):
            best_wkt, best_runs = w, r
    best_bowling = f"{best_wkt}/{best_runs}" if innings_bowled > 0 else "0/0"

    return PlayerCareerStats(
        player_id=player_id,
        player_name=player.name,
        matches=len(match_ids),
        total_runs=total_runs,
        innings_batted=innings_batted,
        not_outs=not_outs,
        highest_score=highest_score,
        batting_average=batting_average,
        strike_rate=strike_rate,
        fifties=fifties,
        hundreds=hundreds,
        fours=fours,
        sixes=sixes,
        total_wickets=total_wickets,
        innings_bowled=innings_bowled,
        balls_bowled=legal_bowl_balls,
        runs_conceded=runs_conceded,
        best_bowling=best_bowling,
        bowling_average=bowling_average,
        economy=economy,
    )
