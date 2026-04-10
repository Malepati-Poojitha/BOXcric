from sqlalchemy.orm import Session
from app.models.ball import Ball, ExtraType
from app.models.innings import Innings
from app.models.match import Match
from app.models.player import Player
from app.schemas.score import BallInput, LiveScoreOut, BatterStatsOut, BowlerStatsOut, ScorecardOut


def record_ball(db: Session, innings_id: int, data: BallInput) -> Ball:
    """Record a single ball delivery and update innings totals."""
    innings = db.query(Innings).filter(Innings.id == innings_id).first()
    if not innings:
        raise ValueError("Innings not found")
    if innings.is_completed:
        raise ValueError("Innings is already completed")

    match = db.query(Match).filter(Match.id == innings.match_id).first()

    is_legal = data.extra_type not in (ExtraType.WIDE, ExtraType.NO_BALL)

    # Calculate ball/over number
    if is_legal:
        current_ball = innings.total_balls + 1
        over_number = innings.total_overs
        ball_number = current_ball
        if current_ball >= 6:
            innings.total_overs += 1
            innings.total_balls = 0
        else:
            innings.total_balls = current_ball
    else:
        # Illegal delivery — doesn't count as a ball
        over_number = innings.total_overs
        ball_number = innings.total_balls + 1  # display position

    ball = Ball(
        innings_id=innings_id,
        over_number=over_number,
        ball_number=ball_number,
        batter_id=data.batter_id,
        bowler_id=data.bowler_id,
        non_striker_id=data.non_striker_id,
        runs_scored=data.runs_scored,
        extra_type=data.extra_type,
        extra_runs=data.extra_runs,
        is_wicket=data.is_wicket,
        wicket_type=data.wicket_type,
        dismissed_player_id=data.dismissed_player_id,
        fielder_id=data.fielder_id,
        is_legal=is_legal,
        is_correction=data.is_correction,
    )
    db.add(ball)

    # Update innings totals
    total_for_ball = data.runs_scored + data.extra_runs
    innings.total_runs += total_for_ball
    innings.extras += data.extra_runs

    if data.is_wicket:
        innings.total_wickets += 1

    # Check if innings should end (all out or overs completed)
    from app.models.team import TeamPlayer
    team_size = db.query(TeamPlayer).filter(TeamPlayer.team_id == innings.batting_team_id).count()
    max_wickets = max(team_size - 1, 1) if team_size > 0 else 10

    # Super over: only 1 over allowed, 2 wickets max
    is_super_over = innings.innings_number > 2
    if is_super_over:
        overs_limit = 1
        max_wickets = min(max_wickets, 2)  # max 2 wickets in super over
    else:
        overs_limit = match.overs

    if innings.total_wickets >= max_wickets or innings.total_overs >= overs_limit:
        innings.is_completed = True

    # Check if target chased (2nd innings or super over chase innings)
    if innings.innings_number % 2 == 0:  # even numbered innings chase odd ones
        prev_inn = db.query(Innings).filter(
            Innings.match_id == innings.match_id,
            Innings.innings_number == innings.innings_number - 1
        ).first()
        if prev_inn and innings.total_runs > prev_inn.total_runs:
            innings.is_completed = True

    db.commit()
    db.refresh(ball)
    return ball


def get_live_score(db: Session, match_id: int) -> LiveScoreOut:
    """Get current live score for a match."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise ValueError("Match not found")

    # Find current active innings
    innings_list = db.query(Innings).filter(
        Innings.match_id == match_id
    ).order_by(Innings.innings_number).all()

    current = None
    for inn in innings_list:
        if not inn.is_completed:
            current = inn
            break
    if not current:
        current = innings_list[-1] if innings_list else None

    if not current:
        raise ValueError("No innings data")

    overs_str = f"{current.total_overs}.{current.total_balls}"
    total_balls_bowled = current.total_overs * 6 + current.total_balls
    run_rate = round((current.total_runs / total_balls_bowled) * 6, 2) if total_balls_bowled > 0 else 0.0

    target = None
    required_rate = None
    if current.innings_number == 2:
        first_inn = innings_list[0]
        target = first_inn.total_runs + 1
        remaining = (match.overs * 6) - total_balls_bowled
        if remaining > 0:
            needed = target - current.total_runs
            required_rate = round((needed / remaining) * 6, 2)

    # Last ball description
    last_ball_str = None
    last = db.query(Ball).filter(Ball.innings_id == current.id).order_by(Ball.id.desc()).first()
    if last:
        parts = []
        if last.extra_type != "none":
            parts.append(last.extra_type.value.upper())
        if last.runs_scored > 0:
            parts.append(f"{last.runs_scored} run{'s' if last.runs_scored != 1 else ''}")
        if last.is_wicket:
            parts.append(f"WICKET ({last.wicket_type.value})")
        last_ball_str = " + ".join(parts) if parts else "dot ball"

    return LiveScoreOut(
        match_id=match_id,
        innings_number=current.innings_number,
        batting_team=current.batting_team.name,
        bowling_team=current.bowling_team.name,
        total_runs=current.total_runs,
        total_wickets=current.total_wickets,
        overs=overs_str,
        run_rate=run_rate,
        target=target,
        required_rate=required_rate,
        last_ball=last_ball_str,
        status=match.status.value,
    )


def get_scorecard(db: Session, innings_id: int) -> ScorecardOut:
    """Generate full scorecard for an innings."""
    innings = db.query(Innings).filter(Innings.id == innings_id).first()
    if not innings:
        raise ValueError("Innings not found")

    balls = db.query(Ball).filter(Ball.innings_id == innings_id).all()

    # Batting stats
    batter_map: dict[int, dict] = {}
    for b in balls:
        # Add striker
        pid = b.batter_id
        if pid and pid not in batter_map:
            player = db.query(Player).filter(Player.id == pid).first()
            if player:
                batter_map[pid] = {
                    "player_id": pid, "player_name": player.name,
                    "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0,
                }
        # Add non-striker (so they appear in scorecard even if 0 balls faced)
        nsid = b.non_striker_id
        if nsid and nsid not in batter_map:
            ns_player = db.query(Player).filter(Player.id == nsid).first()
            if ns_player:
                batter_map[nsid] = {
                    "player_id": nsid, "player_name": ns_player.name,
                    "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0,
                }
        if pid and pid in batter_map:
            batter_map[pid]["runs"] += b.runs_scored
            if b.is_legal:
                batter_map[pid]["balls_faced"] += 1
            if b.runs_scored == 4:
                batter_map[pid]["fours"] += 1
            elif b.runs_scored == 6:
                batter_map[pid]["sixes"] += 1

    # Build dismissal info
    dismissal_map = {}
    for b in balls:
        if b.is_wicket and b.dismissed_player_id:
            wtype = b.wicket_type.value if b.wicket_type else 'out'
            bowler = db.query(Player).filter(Player.id == b.bowler_id).first()
            fielder = db.query(Player).filter(Player.id == b.fielder_id).first() if b.fielder_id else None
            bname = bowler.name if bowler else ''
            fname = fielder.name if fielder else ''
            if wtype == 'caught':
                dismissal_map[b.dismissed_player_id] = f'c {fname} b {bname}'
            elif wtype == 'bowled':
                dismissal_map[b.dismissed_player_id] = f'b {bname}'
            elif wtype == 'lbw':
                dismissal_map[b.dismissed_player_id] = f'lbw b {bname}'
            elif wtype == 'run_out':
                dismissal_map[b.dismissed_player_id] = f'run out ({fname})' if fname else 'run out'
            elif wtype == 'stumped':
                dismissal_map[b.dismissed_player_id] = f'st {fname} b {bname}'
            elif wtype == 'hit_wicket':
                dismissal_map[b.dismissed_player_id] = f'hit wicket b {bname}'
            elif wtype == 'retired':
                dismissal_map[b.dismissed_player_id] = 'retired'
            else:
                dismissal_map[b.dismissed_player_id] = wtype

    batters = []
    for stats in batter_map.values():
        sr = round((stats["runs"] / stats["balls_faced"]) * 100, 2) if stats["balls_faced"] > 0 else 0.0
        dismissal = dismissal_map.get(stats["player_id"], "not out")
        batters.append(BatterStatsOut(strike_rate=sr, dismissal=dismissal, **stats))

    # Bowling stats
    bowler_map: dict[int, dict] = {}
    for b in balls:
        pid = b.bowler_id
        if pid not in bowler_map:
            player = db.query(Player).filter(Player.id == pid).first()
            bowler_map[pid] = {
                "player_id": pid, "player_name": player.name,
                "legal_balls": 0, "maidens": 0, "runs_conceded": 0, "wickets": 0,
                "over_runs": {},
            }
        bowler_map[pid]["runs_conceded"] += b.runs_scored + b.extra_runs
        if b.is_legal:
            bowler_map[pid]["legal_balls"] += 1
        if b.is_wicket:
            bowler_map[pid]["wickets"] += 1
        # Track runs per over for maiden calculation
        ov = b.over_number
        bowler_map[pid]["over_runs"].setdefault(ov, 0)
        bowler_map[pid]["over_runs"][ov] += b.runs_scored + b.extra_runs

    bowlers = []
    for stats in bowler_map.values():
        lb = stats["legal_balls"]
        overs_str = f"{lb // 6}.{lb % 6}"
        maidens = sum(1 for r in stats["over_runs"].values() if r == 0)
        eco = round((stats["runs_conceded"] / lb) * 6, 2) if lb > 0 else 0.0
        bowlers.append(BowlerStatsOut(
            player_id=stats["player_id"], player_name=stats["player_name"],
            overs=overs_str, maidens=maidens, runs_conceded=stats["runs_conceded"],
            wickets=stats["wickets"], economy=eco,
        ))

    overs_str = f"{innings.total_overs}.{innings.total_balls}"
    return ScorecardOut(
        match_id=innings.match_id, innings_number=innings.innings_number,
        batting_team=innings.batting_team.name,
        total_runs=innings.total_runs, total_wickets=innings.total_wickets,
        overs=overs_str, batters=batters, bowlers=bowlers,
    )
