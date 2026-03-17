from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class TeamPlayer(Base):
    __tablename__ = "team_players"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    short_name = Column(String(10), nullable=True)
    captain_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    vice_captain_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    players = relationship("Player", secondary="team_players", lazy="joined")
    captain = relationship("Player", foreign_keys=[captain_id], lazy="joined")
    vice_captain = relationship("Player", foreign_keys=[vice_captain_id], lazy="joined")
