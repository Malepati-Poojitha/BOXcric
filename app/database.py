from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_libsql = DATABASE_URL.startswith("libsql")

# Register libsql dialect with SQLAlchemy
if _is_libsql:
    import sqlalchemy_libsql  # noqa: F401

connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    **({"pool_recycle": 300} if not _is_libsql else {}),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
