"""Service to create notifications for users participating in a match."""
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.match import Match
from app.models.team import TeamPlayer
from app.models.player import Player


def get_match_user_ids(db: Session, match: Match) -> set[int]:
    """Get all user_ids of players in both teams of a match, plus host/cohost."""
    user_ids = set()
    for team_id in [match.team1_id, match.team2_id]:
        # Players linked to users
        rows = (
            db.query(Player.user_id)
            .join(TeamPlayer, TeamPlayer.player_id == Player.id)
            .filter(TeamPlayer.team_id == team_id, Player.user_id.isnot(None))
            .all()
        )
        for (uid,) in rows:
            user_ids.add(uid)
    # Also include team hosts/cohosts
    from app.models.team import Team
    for team_id in [match.team1_id, match.team2_id]:
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            if team.host_id:
                user_ids.add(team.host_id)
            if team.cohost_id:
                user_ids.add(team.cohost_id)
    return user_ids


def notify_match_users(db: Session, match: Match, notif_type: str, title: str, message: str):
    """Create a notification for every user involved in the match."""
    user_ids = get_match_user_ids(db, match)
    for uid in user_ids:
        db.add(Notification(
            user_id=uid,
            match_id=match.id,
            type=notif_type,
            title=title,
            message=message,
        ))
    db.commit()
