from sqlalchemy.orm import Session
from app.models.ball import Ball
from app.models.innings import Innings
from app.models.match import Match, MatchStatus
from app.models.player import Player


def get_all_rankings(db: Session):
    """Calculate batting, bowling, and all-rounder rankings from match data."""
    completed_matches = db.query(Match).filter(Match.status == MatchStatus.COMPLETED).all()
    if not completed_matches:
        return {"batting": [], "bowling": [], "allrounder": []}

    completed_ids = [m.id for m in completed_matches]
    completed_innings = db.query(Innings).filter(Innings.match_id.in_(completed_ids)).all()
    innings_ids = [inn.id for inn in completed_innings]
    all_balls = db.query(Ball).filter(Ball.innings_id.in_(innings_ids)).all()

    if not all_balls:
        return {"batting": [], "bowling": [], "allrounder": []}

    # Map innings_id -> match_id
    innings_match = {inn.id: inn.match_id for inn in completed_innings}

    # ===== BATTING STATS =====
    bat_stats = {}  # player_id -> stats dict
    for b in all_balls:
        pid = b.batter_id
        if pid not in bat_stats:
            bat_stats[pid] = {
                "runs": 0, "balls": 0, "fours": 0, "sixes": 0,
                "innings_runs": {},  # innings_id -> runs
                "match_ids": set(), "dismissed": 0,
            }
        s = bat_stats[pid]
        s["runs"] += b.runs_scored
        if b.is_legal:
            s["balls"] += 1
        if b.runs_scored == 4:
            s["fours"] += 1
        elif b.runs_scored == 6:
            s["sixes"] += 1
        s["innings_runs"].setdefault(b.innings_id, 0)
        s["innings_runs"][b.innings_id] += b.runs_scored
        mid = innings_match.get(b.innings_id)
        if mid:
            s["match_ids"].add(mid)

    # Count dismissals
    for b in all_balls:
        if b.is_wicket and b.dismissed_player_id and b.dismissed_player_id in bat_stats:
            bat_stats[b.dismissed_player_id]["dismissed"] += 1

    batting_ranks = []
    for pid, s in bat_stats.items():
        player = db.query(Player).filter(Player.id == pid).first()
        if not player:
            continue
        matches = len(s["match_ids"])
        innings = len(s["innings_runs"])
        runs = s["runs"]
        balls = s["balls"]
        not_outs = innings - s["dismissed"]
        dismissals = s["dismissed"]
        avg = round(runs / dismissals, 2) if dismissals > 0 else float(runs)
        sr = round((runs / balls) * 100, 2) if balls > 0 else 0.0
        hs = max(s["innings_runs"].values()) if s["innings_runs"] else 0
        fifties = sum(1 for r in s["innings_runs"].values() if 50 <= r < 100)
        hundreds = sum(1 for r in s["innings_runs"].values() if r >= 100)

        # Batting rating: weighted formula
        # Runs(40%) + Average(25%) + Strike Rate(15%) + Boundary bonus(10%) + Consistency(10%)
        rating = (
            (min(runs, 500) / 500) * 40 +
            (min(avg, 60) / 60) * 25 +
            (min(sr, 200) / 200) * 15 +
            (min(s["fours"] + s["sixes"] * 2, 100) / 100) * 10 +
            (min(innings, 20) / 20) * 10
        )

        batting_ranks.append({
            "player_id": pid, "player_name": player.name,
            "matches": matches, "innings": innings, "runs": runs,
            "balls_faced": balls, "not_outs": not_outs,
            "highest_score": hs, "average": avg, "strike_rate": sr,
            "fours": s["fours"], "sixes": s["sixes"],
            "fifties": fifties, "hundreds": hundreds,
            "rating": round(rating, 1),
        })

    batting_ranks.sort(key=lambda x: x["rating"], reverse=True)
    for i, r in enumerate(batting_ranks):
        r["rank"] = i + 1

    # ===== BOWLING STATS =====
    bowl_stats = {}  # player_id -> stats dict
    for b in all_balls:
        pid = b.bowler_id
        if not pid:
            continue
        if pid not in bowl_stats:
            bowl_stats[pid] = {
                "wickets": 0, "runs_conceded": 0, "balls": 0,
                "innings_wickets": {},  # innings_id -> {w, r}
                "match_ids": set(),
            }
        s = bowl_stats[pid]
        s["runs_conceded"] += b.runs_scored + b.extra_runs
        if b.is_legal:
            s["balls"] += 1
        if b.is_wicket:
            s["wickets"] += 1
        s["innings_wickets"].setdefault(b.innings_id, {"w": 0, "r": 0})
        s["innings_wickets"][b.innings_id]["r"] += b.runs_scored + b.extra_runs
        if b.is_wicket:
            s["innings_wickets"][b.innings_id]["w"] += 1
        mid = innings_match.get(b.innings_id)
        if mid:
            s["match_ids"].add(mid)

    bowling_ranks = []
    for pid, s in bowl_stats.items():
        player = db.query(Player).filter(Player.id == pid).first()
        if not player:
            continue
        matches = len(s["match_ids"])
        innings = len(s["innings_wickets"])
        wickets = s["wickets"]
        runs_conceded = s["runs_conceded"]
        balls = s["balls"]
        overs = balls // 6
        rem_balls = balls % 6
        overs_str = f"{overs}.{rem_balls}"
        economy = round((runs_conceded / balls) * 6, 2) if balls > 0 else 0.0
        avg = round(runs_conceded / wickets, 2) if wickets > 0 else 0.0
        sr_bowl = round(balls / wickets, 1) if wickets > 0 else 0.0

        # Best bowling
        best_w, best_r = 0, 999
        for iw in s["innings_wickets"].values():
            if iw["w"] > best_w or (iw["w"] == best_w and iw["r"] < best_r):
                best_w, best_r = iw["w"], iw["r"]
        best = f"{best_w}/{best_r}" if innings > 0 else "0/0"

        # 3-wicket hauls and 5-wicket hauls
        three_w = sum(1 for iw in s["innings_wickets"].values() if iw["w"] >= 3)
        five_w = sum(1 for iw in s["innings_wickets"].values() if iw["w"] >= 5)

        # Bowling rating: Wickets(35%) + Economy(25%) + Average(20%) + Strike Rate(10%) + Consistency(10%)
        eco_score = max(0, (12 - min(economy, 12)) / 12) if economy > 0 else 0
        avg_score = max(0, (40 - min(avg, 40)) / 40) if avg > 0 else 0
        sr_score = max(0, (30 - min(sr_bowl, 30)) / 30) if sr_bowl > 0 else 0

        rating = (
            (min(wickets, 30) / 30) * 35 +
            eco_score * 25 +
            avg_score * 20 +
            sr_score * 10 +
            (min(innings, 20) / 20) * 10
        )

        bowling_ranks.append({
            "player_id": pid, "player_name": player.name,
            "matches": matches, "innings": innings, "wickets": wickets,
            "overs": overs_str, "runs_conceded": runs_conceded,
            "economy": economy, "average": avg, "strike_rate": sr_bowl,
            "best_bowling": best, "three_wickets": three_w, "five_wickets": five_w,
            "rating": round(rating, 1),
        })

    bowling_ranks.sort(key=lambda x: x["rating"], reverse=True)
    for i, r in enumerate(bowling_ranks):
        r["rank"] = i + 1

    # ===== ALL-ROUNDER STATS =====
    allrounder_ranks = []
    all_player_ids = set(bat_stats.keys()) | set(bowl_stats.keys())

    for pid in all_player_ids:
        bs = bat_stats.get(pid)
        bw = bowl_stats.get(pid)

        # Must have both batting and bowling to qualify
        if not bs or not bw:
            continue
        if bs["runs"] < 1 and bw["wickets"] < 1:
            continue

        player = db.query(Player).filter(Player.id == pid).first()
        if not player:
            continue

        bat_rating = 0
        bowl_rating = 0

        # Find this player's batting rating
        for br in batting_ranks:
            if br["player_id"] == pid:
                bat_rating = br["rating"]
                break

        # Find this player's bowling rating
        for bwr in bowling_ranks:
            if bwr["player_id"] == pid:
                bowl_rating = bwr["rating"]
                break

        # All-rounder rating: average of batting and bowling ratings
        # Bonus for being good at both (balance factor)
        balance = min(bat_rating, bowl_rating) / max(bat_rating, bowl_rating, 1)
        ar_rating = (bat_rating + bowl_rating) / 2 * (0.7 + 0.3 * balance)

        all_matches = bs["match_ids"] | bw["match_ids"]

        allrounder_ranks.append({
            "player_id": pid, "player_name": player.name,
            "matches": len(all_matches),
            "runs": bs["runs"],
            "batting_avg": round(bs["runs"] / bs["dismissed"], 2) if bs["dismissed"] > 0 else float(bs["runs"]),
            "batting_sr": round((bs["runs"] / bs["balls"]) * 100, 2) if bs["balls"] > 0 else 0.0,
            "wickets": bw["wickets"],
            "bowling_eco": round((bw["runs_conceded"] / bw["balls"]) * 6, 2) if bw["balls"] > 0 else 0.0,
            "bowling_avg": round(bw["runs_conceded"] / bw["wickets"], 2) if bw["wickets"] > 0 else 0.0,
            "bat_rating": round(bat_rating, 1),
            "bowl_rating": round(bowl_rating, 1),
            "rating": round(ar_rating, 1),
        })

    allrounder_ranks.sort(key=lambda x: x["rating"], reverse=True)
    for i, r in enumerate(allrounder_ranks):
        r["rank"] = i + 1

    return {
        "batting": batting_ranks,
        "bowling": bowling_ranks,
        "allrounder": allrounder_ranks,
    }
