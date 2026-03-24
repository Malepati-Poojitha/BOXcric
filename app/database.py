from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_libsql = DATABASE_URL.startswith("libsql")

if _is_libsql:
    import libsql_experimental as libsql
    from urllib.parse import urlparse, parse_qs

    _parsed = urlparse(DATABASE_URL)
    _turso_url = f"libsql://{_parsed.hostname}"
    _auth_token = parse_qs(_parsed.query).get("authToken", [""])[0]

    # Single shared libsql connection — reads/writes go through Turso sync
    _turso_conn = libsql.connect(
        "turso_replica.db", sync_url=_turso_url, auth_token=_auth_token
    )
    _turso_conn.sync()

    class _LibsqlConnectionWrapper:
        """Wraps libsql connection so SQLAlchemy can use it as a DBAPI connection."""
        def __init__(self):
            self._conn = _turso_conn
        def cursor(self):
            return self._conn.cursor()
        def commit(self):
            self._conn.commit()
            self._conn.sync()
        def rollback(self):
            self._conn.rollback()
        def close(self):
            pass  # Keep connection alive
        def execute(self, *args, **kwargs):
            return self._conn.execute(*args, **kwargs)
        def create_function(self, *a, **kw):
            pass
        @property
        def isolation_level(self):
            return ""
        @isolation_level.setter
        def isolation_level(self, val):
            pass
        @property
        def in_transaction(self):
            return False
        def __getattr__(self, name):
            return getattr(self._conn, name)

    engine = create_engine(
        "sqlite://",
        creator=lambda: _LibsqlConnectionWrapper(),
        connect_args={"check_same_thread": False},
    )

elif _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        pool_recycle=300,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
