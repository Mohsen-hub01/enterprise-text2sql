import os
from pathlib import Path
from sqlalchemy import text


from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not defined")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def test_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar()




def execute_query(sql: str):
    with engine.connect() as connection:
        result = connection.execute(text(sql))

        columns = result.keys()
        rows = result.fetchall()

        return [
            dict(zip(columns, row))
            for row in rows
        ]