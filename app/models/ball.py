from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ExtraType(str, enum.Enum):
    NONE = "none"
    WIDE = "wide"
    NO_BALL = "no_ball"
    BYE = "bye"
    LEG_BYE = "leg_bye"


class WicketType(str, enum.Enum):
    NONE = "none"
    BOWLED = "bowled"
    CAUGHT = "caught"
    LBW = "lbw"
    RUN_OUT = "run_out"
    STUMPED = "stumped"
    HIT_WICKET = "hit_wicket"
    RETIRED = "retired"


class Ball(Base):
    __tablename__ = "balls"

    id = Column(Integer, primary_key=True, index=True)
    innings_id = Column(Integer, ForeignKey("innings.id"), nullable=False)
    over_number = Column(Integer, nullable=False)      # 0-indexed over
    ball_number = Column(Integer, nullable=False)       # 1-6 within the over
    batter_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    bowler_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    non_striker_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    runs_scored = Column(Integer, default=0)            # runs off the bat
    extra_type = Column(SQLEnum(ExtraType), default=ExtraType.NONE)
    extra_runs = Column(Integer, default=0)
    is_wicket = Column(Boolean, default=False)
    wicket_type = Column(SQLEnum(WicketType), default=WicketType.NONE)
    dismissed_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    fielder_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    is_legal = Column(Boolean, default=True)            # false for wides/no-balls

    innings = relationship("Innings", back_populates="balls")
    batter = relationship("Player", foreign_keys=[batter_id])
    bowler = relationship("Player", foreign_keys=[bowler_id])
    dismissed_player = relationship("Player", foreign_keys=[dismissed_player_id])
