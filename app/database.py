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

    # Use libsql embedded replica: local SQLite file synced with Turso
    _turso_conn = libsql.connect(
        "turso_replica.db", sync_url=_turso_url, auth_token=_auth_token
    )
    _turso_conn.sync()

    # Use a standard SQLite engine on the synced local file for full compatibility
    engine = create_engine(
        "sqlite:///turso_replica.db",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    # Sync changes back to Turso after each session
    from sqlalchemy import event as _sa_event

    @_sa_event.listens_for(engine, "commit")
    def _sync_on_commit(conn):
        try:
            _turso_conn.sync()
        except Exception as e:
            print(f"[TURSO] Sync error: {e}")

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
