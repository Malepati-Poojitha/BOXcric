import os
from dotenv import load_dotenv
load_dotenv()

_db_url = os.getenv("DATABASE_URL", "")
# Render uses postgres:// but SQLAlchemy needs postgresql://
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
# Turso uses libsql:// — convert to the SQLAlchemy driver scheme
if _db_url.startswith("libsql://"):
    _db_url = _db_url.replace("libsql://", "sqlite+libsql://", 1)
# Ignore empty or invalid DATABASE_URL, use SQLite
if not _db_url or not _db_url.startswith(("sqlite", "postgresql", "mysql")):
    DATABASE_URL = "sqlite:///./boxcric.db"
else:
    DATABASE_URL = _db_url
APP_TITLE = "BOXcric"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Manage scores, stats, records & live scores for regular cricket matches"
