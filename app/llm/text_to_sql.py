from app.database.schema import get_database_schema
from app.llm.client import client


def generate_sql(question: str) -> str:
    schema = get_database_schema()

    prompt = f"""
You are an expert PostgreSQL data engineer.

Your task is to convert a natural-language question into one valid PostgreSQL SELECT query.

Database schema:
{schema}

User question:
{question}

Instructions:
- Use ONLY tables and columns present in the schema.
- Respect primary-key and foreign-key relationships.
- Use the foreign-key relationships when JOINs are required.
- Never invent a table or column.
- Generate only SELECT queries.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE or TRUNCATE.
- For revenue questions, use completed orders unless the question explicitly says otherwise.- Return only the SQL query.
- Do not use markdown.
- Do not explain the query.
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

    return response.choices[0].message.content.strip()