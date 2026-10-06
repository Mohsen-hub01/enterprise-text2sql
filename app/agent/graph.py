from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from app.llm.client import client
from app.llm.text_to_sql import generate_sql
from app.guardrails.sql_guard import validate_sql, apply_limit
from app.database.db import execute_query
from app.llm.answer_generator import generate_answer
from app.database.schema import get_database_schema

class AgentState(TypedDict, total=False):
    question: str
    retry_count: int
    execution_error: str
    generated_sql: str
    safe_sql: str

    validation: dict

    results: list

    answer: str

    error: str


def generate_sql_node(state: AgentState):
    sql = generate_sql(state["question"])

    return {
        "generated_sql": sql
    }


def validate_sql_node(state: AgentState):
    validation = validate_sql(
        state["generated_sql"]
    )

    return {
        "validation": validation
    }


def validation_router(state: AgentState):
    if state["validation"]["valid"]:
        return "execute"

    return "blocked"


def execute_node(state: AgentState):
    safe_sql = apply_limit(
        state["generated_sql"]
    )

    try:
        results = execute_query(safe_sql)

        return {
            "safe_sql": safe_sql,
            "results": results,
            "execution_error": "",
        }

    except Exception as exc:
        return {
            "safe_sql": safe_sql,
            "execution_error": str(exc),
        }

MAX_RETRIES = 2


def execution_router(state: AgentState):
    if not state.get("execution_error"):
        return "answer"

    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "failed"

    return "fix_sql"


def answer_node(state: AgentState):
    answer = generate_answer(
        question=state["question"],
        results=state["results"],
    )

    return {
        "answer": answer
    }


def blocked_node(state: AgentState):
    return {
        "error": state["validation"]["reason"],
        "answer": (
            "The generated SQL query was blocked "
            "by the safety guardrails."
        ),
    }
def fix_sql_node(state: AgentState):
    schema = get_database_schema()

    prompt = f"""
You generated a PostgreSQL query that failed.

Database schema:
{schema}

Original question:
{state["question"]}

Failed SQL:
{state["generated_sql"]}

PostgreSQL error:
{state["execution_error"]}

Correct the SQL query.

Rules:
- Return only SQL.
- Generate only SELECT queries.
- Use only tables and columns from the provided schema.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER or CREATE.
- Do not explain anything.
"""

    response = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    corrected_sql = response.choices[0].message.content.strip()

    return {
        "generated_sql": corrected_sql,
        "retry_count": state.get("retry_count", 0) + 1,
        "execution_error": "",
    }


def failed_node(state: AgentState):
    return {
        "answer": "The query could not be executed after multiple correction attempts.",
        "error": state.get("execution_error", "Unknown execution error"),
    }


builder = StateGraph(AgentState)

builder.add_node("generate_sql", generate_sql_node)
builder.add_node("validate_sql", validate_sql_node)
builder.add_node("execute", execute_node)
builder.add_node("answer", answer_node)
builder.add_node("blocked", blocked_node)
builder.add_node("fix_sql", fix_sql_node)
builder.add_node("failed", failed_node)
builder.add_edge(
    START,
    "generate_sql"
)

builder.add_edge(
    "generate_sql",
    "validate_sql"
)

builder.add_conditional_edges(
    "validate_sql",
    validation_router,
    {
        "execute": "execute",
        "blocked": "blocked",
    },
)

builder.add_conditional_edges(
    "execute",
    execution_router,
    {
        "answer": "answer",
        "fix_sql": "fix_sql",
        "failed": "failed",
    },
)

builder.add_edge(
    "fix_sql",
    "validate_sql"
)
builder.add_edge(
    "failed",
    END
)

builder.add_edge(
    "answer",
    END
)

builder.add_edge(
    "blocked",
    END
)


text2sql_graph = builder.compile()