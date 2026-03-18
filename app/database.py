from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
_engine_kwargs = dict(
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)
# libsql (Turso) doesn't support connection pooling options
if "libsql" in DATABASE_URL:
    _engine_kwargs = dict(connect_args=connect_args)
engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
