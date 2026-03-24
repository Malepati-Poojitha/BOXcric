"""All extra features: MOM, Predictions, H2H, Partnerships, Milestones, Photos, Reactions, Undo, Calendar, Fantasy."""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
import os, uuid, json

from app.database import get_db
from app.models.ball import Ball
from app.models.innings import Innings
from app.models.match import Match, MatchStatus
from app.models.player import Player
from app.models.team import Team
from app.models.extras import MatchPhoto, MOMVote, MatchPrediction, Reaction, Milestone
from app.auth import get_current_user_from_cookie

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHOTO_DIR = os.path.join(BASE_DIR, "static", "uploads", "match_photos")
os.makedirs(PHOTO_DIR, exist_ok=True)

router = APIRouter(prefix="/api/features", tags=["Features"])


# ===== 1. MAN OF THE MATCH =====
@router.post("/mom/vote")
def vote_mom(match_id: int, player_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    voter_id = user.id if user else None
    if voter_id:
        existing = db.query(MOMVote).filter(MOMVote.match_id == match_id, MOMVote.voter_id == voter_id).first()
        if existing:
            existing.player_id = player_id
            db.commit()
            return {"detail": "Vote updated"}
    vote = MOMVote(match_id=match_id, player_id=player_id, voter_id=voter_id)
    db.add(vote)
    db.commit()
    return {"detail": "Vote recorded"}


@router.get("/mom/{match_id}")
def get_mom(match_id: int, db: Session = Depends(get_db)):
    votes = db.query(MOMVote.player_id, func.count(MOMVote.id).label("count")).filter(
        MOMVote.match_id == match_id
    ).group_by(MOMVote.player_id).order_by(func.count(MOMVote.id).desc()).all()
    results = []
    for pid, count in votes:
        p = db.query(Player).filter(Player.id == pid).first()
        results.append({"player_id": pid, "player_name": p.name if p else "?", "votes": count})
    return {"match_id": match_id, "votes": results, "winner": results[0] if results else None}


@router.post("/mom/set")
def admin_set_mom(match_id: int, player_id: int, db: Session = Depends(get_db)):
    """Admin sets MOM directly."""
    for _ in range(10):  # add 10 admin votes to override
        db.add(MOMVote(match_id=match_id, player_id=player_id, voter_id=0))
    db.commit()
    return {"detail": "MOM set by admin"}


# ===== 2. MATCH PREDICTIONS =====
@router.post("/predict")
def make_prediction(match_id: int, team_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    existing = db.query(MatchPrediction).filter(
        MatchPrediction.match_id == match_id, MatchPrediction.user_id == user.id
    ).first()
    if existing:
        existing.predicted_winner_id = team_id
        db.commit()
        return {"detail": "Prediction updated"}
    pred = MatchPrediction(match_id=match_id, user_id=user.id, predicted_winner_id=team_id)
    db.add(pred)
    db.commit()
    return {"detail": "Prediction recorded"}


@router.get("/predictions/{match_id}")
def get_predictions(match_id: int, db: Session = Depends(get_db)):
    preds = db.query(MatchPrediction).filter(MatchPrediction.match_id == match_id).all()
    m = db.query(Match).filter(Match.id == match_id).first()
    t1_count = sum(1 for p in preds if p.predicted_winner_id == m.team1_id)
    t2_count = sum(1 for p in preds if p.predicted_winner_id == m.team2_id)
    total = t1_count + t2_count
    return {
        "match_id": match_id,
        "total_predictions": total,
        "team1_id": m.team1_id, "team1_votes": t1_count,
        "team2_id": m.team2_id, "team2_votes": t2_count,
        "team1_pct": round(t1_count / total * 100) if total else 50,
        "team2_pct": round(t2_count / total * 100) if total else 50,
    }


@router.get("/predictions/leaderboard")
def prediction_leaderboard(db: Session = Depends(get_db)):
    """Users ranked by prediction accuracy."""
    from app.models.user import User
    users = db.query(User).all()
    board = []
    for u in users:
        preds = db.query(MatchPrediction).filter(MatchPrediction.user_id == u.id).all()
        total = len(preds)
        if total == 0:
            continue
        correct = 0
        for p in preds:
            m = db.query(Match).filter(Match.id == p.match_id).first()
            if m and m.winner_id and m.winner_id == p.predicted_winner_id:
                correct += 1
        board.append({
            "user_id": u.id, "user_name": u.name,
            "total": total, "correct": correct,
            "accuracy": round(correct / total * 100, 1) if total else 0,
        })
    board.sort(key=lambda x: (-x["correct"], -x["accuracy"]))
    return board


# ===== 3. EMOJI REACTIONS =====
@router.post("/react")
def add_reaction(match_id: int, emoji: str, ball_id: int = None, request: Request = None, db: Session = Depends(get_db)):
    if emoji not in ["🔥", "🎉", "😱", "👏", "💔", "😂"]:
        raise HTTPException(status_code=400, detail="Invalid emoji")
    user = get_current_user_from_cookie(request, db) if request else None
    r = Reaction(match_id=match_id, ball_id=ball_id, user_id=user.id if user else None, emoji=emoji)
    db.add(r)
    db.commit()
    return {"detail": "Reaction added"}


@router.get("/reactions/{match_id}")
def get_reactions(match_id: int, db: Session = Depends(get_db)):
    reacts = db.query(Reaction.emoji, func.count(Reaction.id)).filter(
        Reaction.match_id == match_id
    ).group_by(Reaction.emoji).all()
    return {emoji: count for emoji, count in reacts}


# ===== 4. UNDO LAST BALL =====
@router.delete("/undo/{innings_id}")
def undo_last_ball(innings_id: int, db: Session = Depends(get_db)):
    """Undo the last scored ball. Each ball position allows only one correction."""
    last_ball = db.query(Ball).filter(Ball.innings_id == innings_id).order_by(Ball.id.desc()).first()
    if not last_ball:
        raise HTTPException(status_code=404, detail="No balls to undo")

    if last_ball.is_correction:
        raise HTTPException(status_code=400, detail="This ball was already corrected once. No further undo allowed.")

    inn = db.query(Innings).filter(Innings.id == innings_id).first()
    if not inn:
        raise HTTPException(status_code=404, detail="Innings not found")

    # Reverse the ball's effect on innings
    inn.total_runs -= (last_ball.runs_scored + last_ball.extra_runs)
    inn.extras -= last_ball.extra_runs
    if last_ball.is_wicket:
        inn.total_wickets -= 1
    if last_ball.is_legal:
        if inn.total_balls > 0:
            inn.total_balls -= 1
        else:
            inn.total_overs -= 1
            inn.total_balls = 5
    inn.is_completed = False

    ball_info = f"{last_ball.over_number}.{last_ball.ball_number} | {last_ball.runs_scored}runs"
    db.delete(last_ball)
    db.commit()
    return {"detail": f"Last ball undone: {ball_info}. Score the correct ball now (one-time correction).", "is_correction": True}


# ===== 5. HEAD-TO-HEAD =====
@router.get("/h2h/{player1_id}/{player2_id}")
def head_to_head(player1_id: int, player2_id: int, db: Session = Depends(get_db)):
    """How player1 performed against player2's bowling and vice versa."""
    p1 = db.query(Player).filter(Player.id == player1_id).first()
    p2 = db.query(Player).filter(Player.id == player2_id).first()
    if not p1 or not p2:
        raise HTTPException(status_code=404, detail="Player not found")

    # P1 batting vs P2 bowling
    p1_vs_p2 = db.query(Ball).filter(Ball.batter_id == player1_id, Ball.bowler_id == player2_id).all()
    p1_runs = sum(b.runs_scored for b in p1_vs_p2)
    p1_balls = sum(1 for b in p1_vs_p2 if b.is_legal)
    p1_dismissed = sum(1 for b in p1_vs_p2 if b.is_wicket and b.dismissed_player_id == player1_id)
    p1_fours = sum(1 for b in p1_vs_p2 if b.runs_scored == 4)
    p1_sixes = sum(1 for b in p1_vs_p2 if b.runs_scored == 6)

    # P2 batting vs P1 bowling
    p2_vs_p1 = db.query(Ball).filter(Ball.batter_id == player2_id, Ball.bowler_id == player1_id).all()
    p2_runs = sum(b.runs_scored for b in p2_vs_p1)
    p2_balls = sum(1 for b in p2_vs_p1 if b.is_legal)
    p2_dismissed = sum(1 for b in p2_vs_p1 if b.is_wicket and b.dismissed_player_id == player2_id)
    p2_fours = sum(1 for b in p2_vs_p1 if b.runs_scored == 4)
    p2_sixes = sum(1 for b in p2_vs_p1 if b.runs_scored == 6)

    return {
        "player1": {"id": player1_id, "name": p1.name,
                     "runs_vs": p1_runs, "balls_faced": p1_balls, "dismissed_by": p1_dismissed,
                     "fours": p1_fours, "sixes": p1_sixes,
                     "sr": round(p1_runs / p1_balls * 100, 1) if p1_balls else 0},
        "player2": {"id": player2_id, "name": p2.name,
                     "runs_vs": p2_runs, "balls_faced": p2_balls, "dismissed_by": p2_dismissed,
                     "fours": p2_fours, "sixes": p2_sixes,
                     "sr": round(p2_runs / p2_balls * 100, 1) if p2_balls else 0},
    }


# ===== 6. TEAM VS TEAM HISTORY =====
@router.get("/team-vs-team/{team1_id}/{team2_id}")
def team_vs_team(team1_id: int, team2_id: int, db: Session = Depends(get_db)):
    matches = db.query(Match).filter(
        Match.status == MatchStatus.COMPLETED,
        ((Match.team1_id == team1_id) & (Match.team2_id == team2_id)) |
        ((Match.team1_id == team2_id) & (Match.team2_id == team1_id))
    ).all()
    t1 = db.query(Team).filter(Team.id == team1_id).first()
    t2 = db.query(Team).filter(Team.id == team2_id).first()
    t1_wins = sum(1 for m in matches if m.winner_id == team1_id)
    t2_wins = sum(1 for m in matches if m.winner_id == team2_id)
    ties = len(matches) - t1_wins - t2_wins

    # Avg scores
    t1_scores, t2_scores = [], []
    for m in matches:
        innings = db.query(Innings).filter(Innings.match_id == m.id).all()
        for inn in innings:
            if inn.batting_team_id == team1_id:
                t1_scores.append(inn.total_runs)
            elif inn.batting_team_id == team2_id:
                t2_scores.append(inn.total_runs)

    return {
        "team1": {"id": team1_id, "name": t1.name if t1 else "?", "wins": t1_wins,
                  "avg_score": round(sum(t1_scores) / len(t1_scores), 1) if t1_scores else 0},
        "team2": {"id": team2_id, "name": t2.name if t2 else "?", "wins": t2_wins,
                  "avg_score": round(sum(t2_scores) / len(t2_scores), 1) if t2_scores else 0},
        "total_matches": len(matches), "ties": ties,
        "matches": [{"id": m.id, "title": m.title, "winner_id": m.winner_id, "result": m.result_summary} for m in matches[-10:]],
    }


# ===== 7. PARTNERSHIP TRACKER =====
@router.get("/partnerships/{innings_id}")
def get_partnerships(innings_id: int, db: Session = Depends(get_db)):
    """Compute batting partnerships for an innings."""
    balls = db.query(Ball).filter(Ball.innings_id == innings_id).order_by(Ball.id).all()
    if not balls:
        return []

    partnerships = []
    current_pair = set()
    current_runs = 0
    current_balls = 0
    wicket_num = 0

    for b in balls:
        pair = frozenset([b.batter_id, b.non_striker_id]) if b.non_striker_id else frozenset([b.batter_id])
        if not current_pair:
            current_pair = pair

        if pair != current_pair and current_pair:
            # Partnership ended
            names = []
            for pid in current_pair:
                p = db.query(Player).filter(Player.id == pid).first()
                names.append(p.name if p else "?")
            partnerships.append({
                "wicket": wicket_num, "pair": " & ".join(names),
                "runs": current_runs, "balls": current_balls,
            })
            current_pair = pair
            current_runs = 0
            current_balls = 0

        current_runs += b.runs_scored + b.extra_runs
        if b.is_legal:
            current_balls += 1

        if b.is_wicket:
            wicket_num += 1
            names = []
            for pid in current_pair:
                p = db.query(Player).filter(Player.id == pid).first()
                names.append(p.name if p else "?")
            partnerships.append({
                "wicket": wicket_num, "pair": " & ".join(names),
                "runs": current_runs, "balls": current_balls,
            })
            current_pair = set()
            current_runs = 0
            current_balls = 0

    # Last unbroken partnership
    if current_pair and current_runs > 0:
        names = []
        for pid in current_pair:
            p = db.query(Player).filter(Player.id == pid).first()
            names.append(p.name if p else "?")
        partnerships.append({
            "wicket": wicket_num, "pair": " & ".join(names),
            "runs": current_runs, "balls": current_balls, "not_out": True,
        })

    return partnerships


# ===== 8. MILESTONES & ACHIEVEMENTS =====
@router.get("/milestones")
def get_all_milestones(db: Session = Depends(get_db)):
    return [{"id": m.id, "player_id": m.player_id, "badge": m.badge, "title": m.title,
             "description": m.description, "created_at": str(m.created_at)}
            for m in db.query(Milestone).order_by(Milestone.created_at.desc()).limit(50).all()]


@router.get("/milestones/check/{match_id}")
def check_milestones(match_id: int, db: Session = Depends(get_db)):
    """Check and award milestones after a match."""
    innings_list = db.query(Innings).filter(Innings.match_id == match_id).all()
    awarded = []

    for inn in innings_list:
        balls = db.query(Ball).filter(Ball.innings_id == inn.id).all()
        batter_runs = {}
        bowler_wickets = {}

        for b in balls:
            batter_runs.setdefault(b.batter_id, 0)
            batter_runs[b.batter_id] += b.runs_scored
            if b.is_wicket and b.bowler_id:
                bowler_wickets.setdefault(b.bowler_id, 0)
                bowler_wickets[b.bowler_id] += 1

        for pid, runs in batter_runs.items():
            p = db.query(Player).filter(Player.id == pid).first()
            if not p:
                continue
            if runs >= 100:
                if not db.query(Milestone).filter(Milestone.player_id == pid, Milestone.match_id == match_id, Milestone.badge == "century").first():
                    m = Milestone(player_id=pid, match_id=match_id, badge="century", title=f"💯 Century! {p.name} scored {runs}", description=f"Scored {runs} runs")
                    db.add(m)
                    awarded.append(m.title)
            elif runs >= 50:
                if not db.query(Milestone).filter(Milestone.player_id == pid, Milestone.match_id == match_id, Milestone.badge == "fifty").first():
                    m = Milestone(player_id=pid, match_id=match_id, badge="fifty", title=f"🔥 Half Century! {p.name} scored {runs}", description=f"Scored {runs} runs")
                    db.add(m)
                    awarded.append(m.title)

        for pid, wkts in bowler_wickets.items():
            p = db.query(Player).filter(Player.id == pid).first()
            if not p:
                continue
            if wkts >= 5:
                if not db.query(Milestone).filter(Milestone.player_id == pid, Milestone.match_id == match_id, Milestone.badge == "five_wickets").first():
                    m = Milestone(player_id=pid, match_id=match_id, badge="five_wickets", title=f"🎯 5-Wicket Haul! {p.name} took {wkts}", description=f"Took {wkts} wickets")
                    db.add(m)
                    awarded.append(m.title)
            elif wkts >= 3:
                if not db.query(Milestone).filter(Milestone.player_id == pid, Milestone.match_id == match_id, Milestone.badge == "three_wickets").first():
                    m = Milestone(player_id=pid, match_id=match_id, badge="three_wickets", title=f"⭐ 3-Wicket Haul! {p.name} took {wkts}", description=f"Took {wkts} wickets")
                    db.add(m)
                    awarded.append(m.title)

    db.commit()
    return {"awarded": awarded}


# ===== 9. PLAYER OF THE MONTH =====
@router.get("/potm")
def player_of_the_month(db: Session = Depends(get_db)):
    """Auto-calculated Player of the Month from recent matches."""
    from app.services.rankings import get_all_rankings
    rankings = get_all_rankings(db)
    result = {}
    if rankings["batting"]:
        result["best_batter"] = rankings["batting"][0]
    if rankings["bowling"]:
        result["best_bowler"] = rankings["bowling"][0]
    if rankings["allrounder"]:
        result["best_allrounder"] = rankings["allrounder"][0]
    return result


# ===== 10. MATCH PHOTOS =====
@router.post("/photos/upload")
async def upload_match_photo(
    request: Request, match_id: int = Form(...),
    caption: str = Form(None), photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only JPG/PNG/WEBP")
    contents = await photo.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Max 10MB")
    ext = photo.filename.rsplit(".", 1)[-1] if "." in photo.filename else "jpg"
    filename = f"m{match_id}_{uuid.uuid4().hex[:8]}.{ext}"
    with open(os.path.join(PHOTO_DIR, filename), "wb") as f:
        f.write(contents)
    user = get_current_user_from_cookie(request, db)
    mp = MatchPhoto(match_id=match_id, photo_url=f"/static/uploads/match_photos/{filename}",
                    caption=caption, uploaded_by=user.name if user else "Admin")
    db.add(mp)
    db.commit()
    return {"detail": "Photo uploaded", "url": mp.photo_url}


@router.get("/photos/{match_id}")
def get_match_photos(match_id: int, db: Session = Depends(get_db)):
    photos = db.query(MatchPhoto).filter(MatchPhoto.match_id == match_id).order_by(MatchPhoto.created_at.desc()).all()
    return [{"id": p.id, "url": p.photo_url, "caption": p.caption,
             "uploaded_by": p.uploaded_by, "created_at": str(p.created_at)} for p in photos]


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    p = db.query(MatchPhoto).filter(MatchPhoto.id == photo_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    filepath = os.path.join(BASE_DIR, p.photo_url.lstrip("/"))
    if os.path.exists(filepath):
        os.remove(filepath)
    db.delete(p)
    db.commit()
    return {"detail": "Deleted"}


# ===== 11. SCHEDULE CALENDAR =====
@router.get("/calendar")
def match_calendar(db: Session = Depends(get_db)):
    """All matches grouped by date for calendar view."""
    matches = db.query(Match).order_by(Match.date).all()
    calendar = {}
    for m in matches:
        date_str = m.date.strftime("%Y-%m-%d") if m.date else "undated"
        if date_str not in calendar:
            calendar[date_str] = []
        t1 = db.query(Team).filter(Team.id == m.team1_id).first()
        t2 = db.query(Team).filter(Team.id == m.team2_id).first()
        calendar[date_str].append({
            "id": m.id, "title": m.title or f"{t1.name if t1 else '?'} vs {t2.name if t2 else '?'}",
            "status": m.status.value, "venue": m.venue,
            "team1": t1.name if t1 else "?", "team2": t2.name if t2 else "?",
            "result": m.result_summary,
        })
    return calendar


# ===== 12. TOSS COIN FLIP =====
@router.get("/toss-result/{match_id}")
def toss_result(match_id: int, db: Session = Depends(get_db)):
    m = db.query(Match).filter(Match.id == match_id).first()
    if not m or not m.toss_winner_id:
        return {"toss_done": False}
    t = db.query(Team).filter(Team.id == m.toss_winner_id).first()
    return {
        "toss_done": True,
        "winner": t.name if t else "?",
        "decision": m.toss_decision.value if m.toss_decision else "?",
    }


# ===== 13. FANTASY CRICKET (Simple) =====
_fantasy_teams = {}  # in-memory: { "match_id:user_id": [player_ids] }

@router.post("/fantasy/pick")
def fantasy_pick(match_id: int, player_ids: list[int], request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if len(player_ids) > 11:
        raise HTTPException(status_code=400, detail="Max 11 players")
    key = f"{match_id}:{user.id}"
    _fantasy_teams[key] = player_ids
    return {"detail": f"Fantasy XI saved ({len(player_ids)} players)"}


@router.get("/fantasy/{match_id}")
def fantasy_scores(match_id: int, request: Request, db: Session = Depends(get_db)):
    """Calculate fantasy points for a user's XI."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return {"detail": "Login to see fantasy"}
    key = f"{match_id}:{user.id}"
    picks = _fantasy_teams.get(key, [])
    if not picks:
        return {"picks": [], "total_points": 0}

    innings_list = db.query(Innings).filter(Innings.match_id == match_id).all()
    inn_ids = [i.id for i in innings_list]
    all_balls = db.query(Ball).filter(Ball.innings_id.in_(inn_ids)).all() if inn_ids else []

    results = []
    total = 0
    for pid in picks:
        p = db.query(Player).filter(Player.id == pid).first()
        pts = 0
        runs = sum(b.runs_scored for b in all_balls if b.batter_id == pid)
        fours = sum(1 for b in all_balls if b.batter_id == pid and b.runs_scored == 4)
        sixes = sum(1 for b in all_balls if b.batter_id == pid and b.runs_scored == 6)
        wkts = sum(1 for b in all_balls if b.bowler_id == pid and b.is_wicket)
        pts += runs + fours * 1 + sixes * 2 + wkts * 25
        if runs >= 50: pts += 20
        if runs >= 100: pts += 50
        if wkts >= 3: pts += 20
        total += pts
        results.append({"player_id": pid, "name": p.name if p else "?",
                        "runs": runs, "wickets": wkts, "points": pts})

    results.sort(key=lambda x: -x["points"])
    return {"picks": results, "total_points": total}


@router.get("/fantasy/leaderboard/{match_id}")
def fantasy_leaderboard(match_id: int, db: Session = Depends(get_db)):
    """Leaderboard of all fantasy teams for a match."""
    from app.models.user import User
    board = []
    for key, picks in _fantasy_teams.items():
        if not key.startswith(f"{match_id}:"):
            continue
        uid = int(key.split(":")[1])
        u = db.query(User).filter(User.id == uid).first()
        innings_list = db.query(Innings).filter(Innings.match_id == match_id).all()
        inn_ids = [i.id for i in innings_list]
        all_balls = db.query(Ball).filter(Ball.innings_id.in_(inn_ids)).all() if inn_ids else []
        total = 0
        for pid in picks:
            runs = sum(b.runs_scored for b in all_balls if b.batter_id == pid)
            fours = sum(1 for b in all_balls if b.batter_id == pid and b.runs_scored == 4)
            sixes = sum(1 for b in all_balls if b.batter_id == pid and b.runs_scored == 6)
            wkts = sum(1 for b in all_balls if b.bowler_id == pid and b.is_wicket)
            total += runs + fours + sixes * 2 + wkts * 25
            if runs >= 50: total += 20
            if runs >= 100: total += 50
        board.append({"user_id": uid, "user_name": u.name if u else "?", "total_points": total})
    board.sort(key=lambda x: -x["total_points"])
    return board
