from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.config import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_libsql = DATABASE_URL.startswith("libsql")

if _is_libsql:
    import libsql_experimental as libsql
    from urllib.parse import urlparse, parse_qs
    import sqlite3

    _parsed = urlparse(DATABASE_URL)
    _turso_url = f"libsql://{_parsed.hostname}"
    _auth_token = parse_qs(_parsed.query).get("authToken", [""])[0]

    class _LibsqlCursorWrapper:
        """Wraps libsql cursor to match sqlite3.Cursor interface."""
        def __init__(self, cursor):
            self._cursor = cursor
            self.description = cursor.description
            self.rowcount = cursor.rowcount
            self.lastrowid = getattr(cursor, 'lastrowid', None)

        def execute(self, sql, params=None):
            if params:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)
            self.description = self._cursor.description
            self.rowcount = self._cursor.rowcount
            self.lastrowid = getattr(self._cursor, 'lastrowid', None)
            return self

        def executemany(self, sql, params_list):
            self._cursor.executemany(sql, params_list)
            self.description = self._cursor.description
            return self

        def fetchone(self):
            return self._cursor.fetchone()

        def fetchmany(self, size=None):
            return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()

        def fetchall(self):
            return self._cursor.fetchall()

        def close(self):
            self._cursor.close()

        def __iter__(self):
            return iter(self._cursor)

    class _LibsqlConnectionWrapper:
        """Wraps libsql Connection to be fully compatible with sqlite3.Connection for SQLAlchemy."""
        def __init__(self):
            self._conn = libsql.connect(
                "turso_replica.db", sync_url=_turso_url, auth_token=_auth_token
            )
            try:
                self._conn.sync()
                print("[TURSO] Initial sync OK")
            except Exception as e:
                print(f"[TURSO] Initial sync warning: {e} — will retry on first query")

        def cursor(self):
            return _LibsqlCursorWrapper(self._conn.cursor())

        def commit(self):
            self._conn.commit()
            try:
                self._conn.sync()
            except Exception as e:
                print(f"[TURSO] Sync after commit warning: {e}")

        def rollback(self):
            self._conn.rollback()

        def close(self):
            pass  # Keep connection alive for reuse

        def execute(self, sql, params=None):
            if params:
                return _LibsqlCursorWrapper(self._conn.execute(sql, params))
            return _LibsqlCursorWrapper(self._conn.execute(sql))

        def create_function(self, *args, **kwargs):
            pass  # Not supported by libsql, but SQLAlchemy pysqlite calls it

        @property
        def isolation_level(self):
            return ""

        @isolation_level.setter
        def isolation_level(self, val):
            pass

        @property
        def in_transaction(self):
            return False

        def __call__(self, *args, **kwargs):
            return self.execute(*args, **kwargs)

    # Create a single shared connection
    _shared_conn = _LibsqlConnectionWrapper()

    engine = create_engine(
        "sqlite://",
        creator=lambda: _shared_conn,
        poolclass=StaticPool,
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
