from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey
from app.database import Base
import enum


class BattingStyle(str, enum.Enum):
    RIGHT_HAND = "right_hand"
    LEFT_HAND = "left_hand"


class BowlingStyle(str, enum.Enum):
    RIGHT_ARM_FAST = "right_arm_fast"
    LEFT_ARM_FAST = "left_arm_fast"
    RIGHT_ARM_MEDIUM = "right_arm_medium"
    LEFT_ARM_MEDIUM = "left_arm_medium"
    RIGHT_ARM_OFFSPIN = "right_arm_offspin"
    LEFT_ARM_ORTHODOX = "left_arm_orthodox"
    RIGHT_ARM_LEGSPIN = "right_arm_legspin"
    LEFT_ARM_CHINAMAN = "left_arm_chinaman"
    NONE = "none"


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    nickname = Column(String(50), nullable=True)
    batting_style = Column(SQLEnum(BattingStyle), default=BattingStyle.RIGHT_HAND)
    bowling_style = Column(SQLEnum(BowlingStyle), default=BowlingStyle.NONE)
    phone = Column(String(15), nullable=True)
    player_role = Column(String(30), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
