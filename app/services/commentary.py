from sqlalchemy.orm import Session
from app.models.ball import Ball, ExtraType, WicketType
from app.models.innings import Innings
from app.models.match import Match
from app.models.player import Player


def get_ball_commentary(db: Session, ball: Ball) -> str:
    """Generate short, clean commentary — boundaries, wickets, extras, dots only."""
    batter = db.query(Player).filter(Player.id == ball.batter_id).first()
    bowler = db.query(Player).filter(Player.id == ball.bowler_id).first()
    bat_name = batter.name if batter else "Batsman"
    bowl_name = bowler.name if bowler else "Bowler"

    over_display = f"{ball.over_number}.{ball.ball_number}"

    # ===== WICKET =====
    if ball.is_wicket:
        dismissed = db.query(Player).filter(Player.id == ball.dismissed_player_id).first()
        dis_name = dismissed.name if dismissed else bat_name
        wtype = ball.wicket_type.value if ball.wicket_type else "out"
        wtype_label = wtype.replace("_", " ").title()
        return f"{over_display} | WICKET! {dis_name} is {wtype_label}. {bowl_name} strikes!"

    # ===== EXTRAS =====
    if ball.extra_type and ball.extra_type.value != "none":
        extra = ball.extra_type.value
        extra_runs = ball.extra_runs

        if extra == "wide":
            return f"{over_display} | Wide, +{extra_runs}"
        if extra == "no_ball":
            return f"{over_display} | No Ball, +{extra_runs}. Free hit!"
        if extra == "bye":
            return f"{over_display} | {extra_runs} Bye{'s' if extra_runs > 1 else ''}"
        if extra == "leg_bye":
            return f"{over_display} | {extra_runs} Leg Bye{'s' if extra_runs > 1 else ''}"

    # ===== RUNS =====
    runs = ball.runs_scored

    if runs == 0:
        return f"{over_display} | Dot ball to {bat_name}"
    if runs == 1:
        return f"{over_display} | 1 run by {bat_name}"
    if runs == 2:
        return f"{over_display} | 2 runs by {bat_name}"
    if runs == 3:
        return f"{over_display} | 3 runs by {bat_name}"
    if runs == 4:
        return f"{over_display} | FOUR! by {bat_name} 🏏"
    if runs == 6:
        return f"{over_display} | SIX! by {bat_name} 🚀"

    return f"{over_display} | {runs} runs by {bat_name}"


def get_match_commentary(db: Session, match_id: int, innings_number: int = None, limit: int = 50) -> list:
    """Get ball-by-ball commentary for a match innings."""
    query = db.query(Innings).filter(Innings.match_id == match_id)
    if innings_number:
        query = query.filter(Innings.innings_number == innings_number)
    innings_list = query.order_by(Innings.innings_number).all()

    commentary = []
    for inn in innings_list:
        balls = db.query(Ball).filter(Ball.innings_id == inn.id).order_by(Ball.id.desc()).limit(limit).all()
        for ball in balls:
            text = get_ball_commentary(db, ball)
            commentary.append({
                "id": ball.id,
                "innings": inn.innings_number,
                "over": ball.over_number,
                "ball": ball.ball_number,
                "text": text,
                "runs": ball.runs_scored + ball.extra_runs,
                "is_wicket": ball.is_wicket,
                "is_four": ball.runs_scored == 4,
                "is_six": ball.runs_scored == 6,
                "is_extra": ball.extra_type and ball.extra_type.value != "none",
            })

    return commentary


def get_over_summary(db: Session, innings_id: int) -> list:
    """Get over-by-over summary with commentary."""
    balls = db.query(Ball).filter(Ball.innings_id == innings_id).order_by(Ball.id).all()
    if not balls:
        return []

    overs = {}
    for b in balls:
        ov = b.over_number
        if ov not in overs:
            overs[ov] = {"over": ov + 1, "balls": [], "runs": 0, "wickets": 0}
        text = get_ball_commentary(db, b)
        overs[ov]["balls"].append({
            "text": text,
            "runs": b.runs_scored + b.extra_runs,
            "is_wicket": b.is_wicket,
            "is_four": b.runs_scored == 4,
            "is_six": b.runs_scored == 6,
        })
        overs[ov]["runs"] += b.runs_scored + b.extra_runs
        if b.is_wicket:
            overs[ov]["wickets"] += 1

    return list(overs.values())
