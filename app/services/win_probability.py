from sqlalchemy.orm import Session
from app.models.ball import Ball
from app.models.innings import Innings
from app.models.match import Match, MatchStatus
from app.models.player import Player, BowlingStyle
from app.models.team import Team


def get_win_probability(db: Session, match_id: int) -> dict:
    """
    Calculate win probability based on:
    - Current score & run rate
    - Wickets fallen (tailenders arrived?)
    - Batting strength remaining
    - All-rounder contributions
    - Required rate vs current rate
    - Historical batting position performance
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        return {"error": "Match not found"}

    innings_list = db.query(Innings).filter(
        Innings.match_id == match_id
    ).order_by(Innings.innings_number).all()

    if not innings_list:
        return {"team1": 50.0, "team2": 50.0, "analysis": "Match not started yet"}

    t1 = db.query(Team).filter(Team.id == match.team1_id).first()
    t2 = db.query(Team).filter(Team.id == match.team2_id).first()
    t1_name = t1.name if t1 else "Team 1"
    t2_name = t2.name if t2 else "Team 2"

    inn1 = innings_list[0] if len(innings_list) > 0 else None
    inn2 = innings_list[1] if len(innings_list) > 1 else None

    # Determine batting/bowling team names for each innings
    bat1_name = t1_name if inn1 and inn1.batting_team_id == match.team1_id else t2_name
    bowl1_name = t2_name if inn1 and inn1.batting_team_id == match.team1_id else t1_name

    # ===== FIRST INNINGS (only inn1 in progress) =====
    if inn1 and not inn1.is_completed and (not inn2 or not inn2.total_runs):
        return _analyze_first_innings(db, match, inn1, bat1_name, bowl1_name)

    # ===== SECOND INNINGS =====
    if inn2 and not inn2.is_completed:
        return _analyze_second_innings(db, match, inn1, inn2, t1_name, t2_name)

    # ===== MATCH COMPLETED =====
    if match.status == MatchStatus.COMPLETED:
        if match.winner_id == match.team1_id:
            return {"team1": 100.0, "team2": 0.0, "team1_name": t1_name, "team2_name": t2_name,
                    "analysis": f"{t1_name} won!", "factors": []}
        elif match.winner_id == match.team2_id:
            return {"team1": 0.0, "team2": 100.0, "team1_name": t1_name, "team2_name": t2_name,
                    "analysis": f"{t2_name} won!", "factors": []}
        else:
            return {"team1": 50.0, "team2": 50.0, "team1_name": t1_name, "team2_name": t2_name,
                    "analysis": "Match Tied!", "factors": []}

    return {"team1": 50.0, "team2": 50.0, "team1_name": t1_name, "team2_name": t2_name,
            "analysis": "Waiting for match to progress", "factors": []}


def _analyze_first_innings(db, match, inn1, bat_name, bowl_name):
    """Analyze during first innings — predict final score."""
    total_balls = inn1.total_overs * 6 + inn1.total_balls
    max_balls = match.overs * 6
    balls_left = max_balls - total_balls

    crr = (inn1.total_runs / total_balls * 6) if total_balls > 0 else 0
    wickets = inn1.total_wickets
    runs = inn1.total_runs

    # Classify batters by position
    batter_analysis = _analyze_batting_lineup(db, inn1)
    factors = []

    # Projected score
    if total_balls > 12:  # at least 2 overs bowled
        # Base projection from current rate
        projected = runs + (crr * balls_left / 6)

        # Adjust for wickets (more wickets = lower projection)
        wicket_factor = 1.0
        if wickets <= 2:
            wicket_factor = 1.05  # batting team doing well
            factors.append(f"Only {wickets} wickets down — strong position")
        elif wickets <= 4:
            wicket_factor = 0.95
            factors.append(f"{wickets} wickets fallen — building pressure")
        elif wickets <= 6:
            wicket_factor = 0.80
            factors.append(f"⚠️ {wickets} wickets down — tailenders approaching")
        elif wickets <= 8:
            wicket_factor = 0.60
            factors.append(f"🔴 {wickets} wickets! Tail exposed")
        else:
            wicket_factor = 0.40
            factors.append(f"🔴 {wickets} wickets! Last pair batting")

        projected *= wicket_factor

        # Analyze who's at crease
        if batter_analysis["tailenders_in"]:
            projected *= 0.85
            factors.append("🏏 Tailender at the crease — run scoring may slow")
        if batter_analysis["allrounder_batting"]:
            projected *= 1.05
            factors.append("⭐ All-rounder at crease — can accelerate")
        if batter_analysis["set_batsman"]:
            projected *= 1.08
            factors.append(f"🔥 Set batsman ({batter_analysis['set_batsman_runs']} runs) — can push the score")

        projected = round(projected)

        # Win probability: higher projected = better for batting team
        # Average T20 score ~ 150-160
        avg_score = match.overs * 7.5
        bat_prob = min(65, max(35, 50 + (projected - avg_score) / avg_score * 30))

        factors.append(f"📊 Projected score: ~{projected}")
        factors.append(f"📈 Current run rate: {round(crr, 2)}")

        return {
            "team1": round(bat_prob if inn1.batting_team_id == match.team1_id else 100 - bat_prob, 1),
            "team2": round(100 - bat_prob if inn1.batting_team_id == match.team1_id else bat_prob, 1),
            "team1_name": bat_name if inn1.batting_team_id == match.team1_id else bowl_name,
            "team2_name": bowl_name if inn1.batting_team_id == match.team1_id else bat_name,
            "analysis": f"{bat_name} projected: ~{projected} | CRR: {round(crr, 2)}",
            "projected_score": projected,
            "factors": factors,
        }

    return {
        "team1": 50.0, "team2": 50.0,
        "team1_name": bat_name, "team2_name": bowl_name,
        "analysis": "Too early to predict — less than 2 overs bowled",
        "factors": ["Need more data for prediction"],
    }


def _analyze_second_innings(db, match, inn1, inn2, t1_name, t2_name):
    """Analyze during chase — who's likely to win."""
    target = inn1.total_runs + 1
    runs_scored = inn2.total_runs
    runs_needed = target - runs_scored
    total_balls = inn2.total_overs * 6 + inn2.total_balls
    max_balls = match.overs * 6
    balls_left = max_balls - total_balls
    wickets = inn2.total_wickets
    wickets_left = 10 - wickets

    crr = (runs_scored / total_balls * 6) if total_balls > 0 else 0
    rrr = (runs_needed / balls_left * 6) if balls_left > 0 else 999

    # Batting team (chasing) and bowling team
    chase_team_id = inn2.batting_team_id
    chase_name = t1_name if chase_team_id == match.team1_id else t2_name
    defend_name = t2_name if chase_team_id == match.team1_id else t1_name

    factors = []
    batter_analysis = _analyze_batting_lineup(db, inn2)

    # ===== CALCULATE WIN PROBABILITY =====
    chase_prob = 50.0  # start neutral

    # 1. Run rate comparison (biggest factor)
    if total_balls >= 6:  # at least 1 over
        if rrr <= 0:
            chase_prob = 99  # already won
        else:
            rate_ratio = crr / rrr if rrr > 0 else 5
            # rate_ratio > 1 means chasing team ahead of required
            rate_factor = (rate_ratio - 1) * 25  # +/-25% per rate difference
            chase_prob += rate_factor
            if rate_ratio > 1.2:
                factors.append(f"📈 Ahead of required rate (CRR {round(crr,1)} > RRR {round(rrr,1)})")
            elif rate_ratio < 0.8:
                factors.append(f"📉 Behind required rate (CRR {round(crr,1)} < RRR {round(rrr,1)})")

    # 2. Wickets factor
    if wickets <= 2:
        chase_prob += 10
        factors.append(f"Strong position — only {wickets} wickets down")
    elif wickets <= 4:
        chase_prob += 3
        factors.append(f"{wickets} wickets fallen — game in balance")
    elif wickets <= 6:
        chase_prob -= 10
        factors.append(f"⚠️ {wickets} wickets down — pressure building")
    elif wickets <= 8:
        chase_prob -= 25
        factors.append(f"🔴 {wickets} wickets! Tailenders at crease")
    else:
        chase_prob -= 40
        factors.append(f"🔴 {wickets} wickets! Last pair — very tough")

    # 3. Balls remaining factor
    overs_left = balls_left / 6
    if balls_left > 0:
        if rrr <= 6 and overs_left > 3:
            chase_prob += 8
            factors.append(f"Comfortable chase — {round(overs_left,1)} overs left at {round(rrr,1)} RRR")
        elif rrr > 12:
            chase_prob -= 15
            factors.append(f"🔥 Needs {round(rrr,1)} per over — very difficult")
        elif rrr > 9:
            chase_prob -= 8
            factors.append(f"Tough ask — {round(rrr,1)} per over needed")

    # 4. Tailender / All-rounder analysis
    if batter_analysis["tailenders_in"] and runs_needed > 30:
        chase_prob -= 12
        factors.append("🏏 Tailender batting — scoring rate likely to drop")
    if batter_analysis["allrounder_batting"]:
        chase_prob += 5
        factors.append("⭐ All-rounder at crease — can finish the chase")
    if batter_analysis["set_batsman"] and runs_needed < 50:
        chase_prob += 8
        factors.append(f"🔥 Set batsman ({batter_analysis['set_batsman_runs']} runs) — can chase this down")

    # 5. Equation summary
    factors.append(f"📊 Need {runs_needed} from {balls_left} balls ({round(overs_left,1)} overs)")
    factors.append(f"Wickets in hand: {wickets_left}")

    # Clamp probability
    chase_prob = max(1, min(99, chase_prob))
    defend_prob = 100 - chase_prob

    # Assign to team1/team2
    if chase_team_id == match.team1_id:
        t1_prob, t2_prob = chase_prob, defend_prob
    else:
        t1_prob, t2_prob = defend_prob, chase_prob

    return {
        "team1": round(t1_prob, 1),
        "team2": round(t2_prob, 1),
        "team1_name": t1_name,
        "team2_name": t2_name,
        "chase_team": chase_name,
        "defend_team": defend_name,
        "target": target,
        "runs_needed": runs_needed,
        "balls_left": balls_left,
        "required_rate": round(rrr, 2),
        "current_rate": round(crr, 2),
        "analysis": f"{chase_name} need {runs_needed} from {balls_left} balls | RRR: {round(rrr,1)}",
        "factors": factors,
    }


def _analyze_batting_lineup(db, innings):
    """Analyze who's currently batting — set batsman? tailender? all-rounder?"""
    balls = db.query(Ball).filter(Ball.innings_id == innings.id).all()
    if not balls:
        return {"tailenders_in": False, "allrounder_batting": False,
                "set_batsman": False, "set_batsman_runs": 0}

    # Get runs per batter
    batter_runs = {}
    batter_balls = {}
    dismissed = set()
    for b in balls:
        batter_runs.setdefault(b.batter_id, 0)
        batter_balls.setdefault(b.batter_id, 0)
        batter_runs[b.batter_id] += b.runs_scored
        if b.is_legal:
            batter_balls[b.batter_id] += 1
        if b.is_wicket and b.dismissed_player_id:
            dismissed.add(b.dismissed_player_id)

    # Find current batters (not dismissed)
    current_batters = [pid for pid in batter_runs if pid not in dismissed]

    # Find the last ball to identify who's at crease
    last_ball = max(balls, key=lambda b: b.id)
    active_ids = set()
    if last_ball.batter_id not in dismissed:
        active_ids.add(last_ball.batter_id)
    if last_ball.non_striker_id and last_ball.non_striker_id not in dismissed:
        active_ids.add(last_ball.non_striker_id)

    tailenders_in = False
    allrounder_batting = False
    set_batsman = False
    set_batsman_runs = 0

    for pid in active_ids:
        player = db.query(Player).filter(Player.id == pid).first()
        if not player:
            continue

        runs = batter_runs.get(pid, 0)
        faced = batter_balls.get(pid, 0)

        # Check if tailender (bowler who can't bat = bowling style not none, batting considered weak)
        # Heuristic: if player has bowled but scored < 10 in 15+ balls = tailender
        bowl_balls = sum(1 for b in balls if b.bowler_id == pid and b.is_legal)
        is_bowler = player.bowling_style and player.bowling_style.value != "none"

        # Batting order position (how many batters came before this one)
        batting_position = len([pid2 for pid2 in batter_runs if pid2 != pid
                                and min((b.id for b in balls if b.batter_id == pid2), default=999)
                                < min((b.id for b in balls if b.batter_id == pid), default=999)]) + 1

        if batting_position >= 8 and is_bowler:
            tailenders_in = True

        if is_bowler and runs >= 15:
            allrounder_batting = True

        if runs >= 20 and faced >= 15:
            set_batsman = True
            if runs > set_batsman_runs:
                set_batsman_runs = runs

    return {
        "tailenders_in": tailenders_in,
        "allrounder_batting": allrounder_batting,
        "set_batsman": set_batsman,
        "set_batsman_runs": set_batsman_runs,
    }
