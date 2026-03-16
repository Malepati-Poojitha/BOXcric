import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./boxcric.db")
APP_TITLE = "BOXcric"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Manage scores, stats, records & live scores for regular cricket matches"
