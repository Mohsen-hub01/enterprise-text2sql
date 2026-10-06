from fastapi import FastAPI
from pydantic import BaseModel
from app.database.schema import get_database_schema
from app.database.db import test_connection
from app.llm.text_to_sql import generate_sql
from app.database.db import execute_query
from app.llm.answer_generator import generate_answer
from app.guardrails.sql_guard import validate_sql, apply_limit
from app.agent.graph import text2sql_graph


class QuestionRequest(BaseModel):
    question: str


app = FastAPI(
    title="Enterprise Text-to-SQL",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "Enterprise Text-to-SQL",
        "status": "running",
    }


@app.get("/health")
def health():
    try:
        database_status = test_connection()

        return {
            "status": "healthy",
            "database": database_status == 1,
        }

    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": False,
            "error": str(exc),
        }



@app.get("/schema")
def schema():
    return get_database_schema()

@app.post("/generate-sql")
def generate_sql_endpoint(request: QuestionRequest):
    sql = generate_sql(request.question)

    validation = validate_sql(sql)

    return {
        "question": request.question,
        "sql": sql,
        "validation": validation,
    }

@app.post("/query")
def query_database(request: QuestionRequest):
    result = text2sql_graph.invoke({
        "question": request.question,
        "retry_count": 0,
    })

    return result