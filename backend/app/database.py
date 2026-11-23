import os
import shutil
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

PROJECT_DB_PATH = Path(__file__).resolve().parents[1] / "dealeros.db"
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]

is_serverless = bool(
    os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
)
is_external_database = DATABASE_URL and not DATABASE_URL.startswith("sqlite")

if is_serverless and not is_external_database:
    DB_PATH = Path("/tmp/dealeros.db")
    if not DB_PATH.exists() and PROJECT_DB_PATH.exists():
        shutil.copy2(PROJECT_DB_PATH, DB_PATH)
    DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"
elif DATABASE_URL:
    if DATABASE_URL.startswith("sqlite:///"):
        sqlite_path = DATABASE_URL[len("sqlite:///"):]
        if sqlite_path and not sqlite_path.startswith(":"):
            Path(sqlite_path).expanduser().resolve().parent.mkdir(
                parents=True, exist_ok=True
            )
else:
    DB_PATH = PROJECT_DB_PATH
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass