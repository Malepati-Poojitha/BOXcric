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

    def sync_to_turso():
        """Sync local replica schema and data to Turso cloud."""
        try:
            import sqlite3
            # Read all DDL from the local file
            local = sqlite3.connect("turso_replica.db")
            schemas = local.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
            ).fetchall()
            local.close()
            # Replay DDL to Turso via libsql (so it reaches the cloud)
            direct = libsql.connect(
                _parsed.hostname, auth_token=_auth_token
            )
            for (sql,) in schemas:
                # Convert CREATE TABLE to IF NOT EXISTS
                safe_sql = sql.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ")
                safe_sql = safe_sql.replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ")
                try:
                    direct.execute(safe_sql)
                except Exception:
                    pass  # table/index already exists
            direct.commit()
            direct.close()
            print("[TURSO] Schema synced to cloud")
        except Exception as e:
            print(f"[TURSO] Schema sync error: {e}")

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
