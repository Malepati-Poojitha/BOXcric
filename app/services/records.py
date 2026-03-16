from sqlalchemy.orm import Session
from app.models.ball import Ball
from app.models.innings import Innings
from app.models.match import Match, MatchStatus
from app.models.player import Player
from app.models.team import Team
from app.schemas.score import RecordOut


def get_all_records(db: Session) -> list[RecordOut]:
    """Compute all-time records across completed matches."""
    records: list[RecordOut] = []

    completed_matches = db.query(Match).filter(Match.status == MatchStatus.COMPLETED).all()
    if not completed_matches:
        return records

    completed_ids = [m.id for m in completed_matches]
    completed_innings = db.query(Innings).filter(Innings.match_id.in_(completed_ids)).all()
    innings_ids = [inn.id for inn in completed_innings]
    all_balls = db.query(Ball).filter(Ball.innings_id.in_(innings_ids)).all()

    if not all_balls:
        return records

    # Map innings_id -> innings for lookups
    innings_map = {inn.id: inn for inn in completed_innings}
    match_map = {m.id: m for m in completed_matches}

    # ---- Highest Individual Score ----
    batter_innings: dict[tuple[int, int], int] = {}  # (player_id, innings_id) -> runs
    for b in all_balls:
        key = (b.batter_id, b.innings_id)
        batter_innings.setdefault(key, 0)
        batter_innings[key] += b.runs_scored

    if batter_innings:
        best_key = max(batter_innings, key=batter_innings.get)
        pid, iid = best_key
        player = db.query(Player).filter(Player.id == pid).first()
        inn = innings_map.get(iid)
        match = match_map.get(inn.match_id) if inn else None
        records.append(RecordOut(
            category="Highest Individual Score",
            value=str(batter_innings[best_key]),
            player_name=player.name if player else "Unknown",
            match_info=match.title or f"Match #{match.id}" if match else None,
        ))

    # ---- Best Bowling in an Innings ----
    bowler_innings: dict[tuple[int, int], dict] = {}
    for b in all_balls:
        if b.bowler_id:
            key = (b.bowler_id, b.innings_id)
            if key not in bowler_innings:
                bowler_innings[key] = {"wickets": 0, "runs": 0}
            bowler_innings[key]["runs"] += b.runs_scored + b.extra_runs
            if b.is_wicket:
                bowler_innings[key]["wickets"] += 1

    if bowler_innings:
        best_bowl_key = max(
            bowler_innings,
            key=lambda k: (bowler_innings[k]["wickets"], -bowler_innings[k]["runs"])
        )
        pid, iid = best_bowl_key
        stats = bowler_innings[best_bowl_key]
        player = db.query(Player).filter(Player.id == pid).first()
        inn = innings_map.get(iid)
        match = match_map.get(inn.match_id) if inn else None
        records.append(RecordOut(
            category="Best Bowling in an Innings",
            value=f"{stats['wickets']}/{stats['runs']}",
            player_name=player.name if player else "Unknown",
            match_info=match.title or f"Match #{match.id}" if match else None,
        ))

    # ---- Highest Team Total ----
    if completed_innings:
        best_inn = max(completed_innings, key=lambda i: i.total_runs)
        team = db.query(Team).filter(Team.id == best_inn.batting_team_id).first()
        match = match_map.get(best_inn.match_id)
        records.append(RecordOut(
            category="Highest Team Total",
            value=f"{best_inn.total_runs}/{best_inn.total_wickets}",
            team_name=team.name if team else "Unknown",
            match_info=match.title or f"Match #{match.id}" if match else None,
        ))

    # ---- Lowest Team Total ----
    if completed_innings:
        worst_inn = min(completed_innings, key=lambda i: i.total_runs)
        team = db.query(Team).filter(Team.id == worst_inn.batting_team_id).first()
        match = match_map.get(worst_inn.match_id)
        records.append(RecordOut(
            category="Lowest Team Total",
            value=f"{worst_inn.total_runs}/{worst_inn.total_wickets}",
            team_name=team.name if team else "Unknown",
            match_info=match.title or f"Match #{match.id}" if match else None,
        ))

    # ---- Most Runs (Career) ----
    career_runs: dict[int, int] = {}
    for b in all_balls:
        career_runs.setdefault(b.batter_id, 0)
        career_runs[b.batter_id] += b.runs_scored
    if career_runs:
        top_pid = max(career_runs, key=career_runs.get)
        player = db.query(Player).filter(Player.id == top_pid).first()
        records.append(RecordOut(
            category="Most Career Runs",
            value=str(career_runs[top_pid]),
            player_name=player.name if player else "Unknown",
        ))

    # ---- Most Wickets (Career) ----
    career_wickets: dict[int, int] = {}
    for b in all_balls:
        if b.is_wicket and b.bowler_id:
            career_wickets.setdefault(b.bowler_id, 0)
            career_wickets[b.bowler_id] += 1
    if career_wickets:
        top_pid = max(career_wickets, key=career_wickets.get)
        player = db.query(Player).filter(Player.id == top_pid).first()
        records.append(RecordOut(
            category="Most Career Wickets",
            value=str(career_wickets[top_pid]),
            player_name=player.name if player else "Unknown",
        ))

    # ---- Most Sixes (Career) ----
    career_sixes: dict[int, int] = {}
    for b in all_balls:
        if b.runs_scored == 6:
            career_sixes.setdefault(b.batter_id, 0)
            career_sixes[b.batter_id] += 1
    if career_sixes:
        top_pid = max(career_sixes, key=career_sixes.get)
        player = db.query(Player).filter(Player.id == top_pid).first()
        records.append(RecordOut(
            category="Most Career Sixes",
            value=str(career_sixes[top_pid]),
            player_name=player.name if player else "Unknown",
        ))

    return records
