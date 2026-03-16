import os

_db_url = os.getenv("DATABASE_URL", "")
# Ignore empty or invalid DATABASE_URL, use SQLite
if not _db_url or not _db_url.startswith(("sqlite", "postgresql", "mysql")):
    DATABASE_URL = "sqlite:///./boxcric.db"
else:
    DATABASE_URL = _db_url
APP_TITLE = "BOXcric"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Manage scores, stats, records & live scores for regular cricket matches"
