from app.llm.client import client


def generate_answer(question: str, results: list) -> str:
    prompt = f"""
You are a data assistant.

Answer the user's question using ONLY the database results provided below.

User question:
{question}

Database results:
{results}

Rules:
- Do not invent information.
- If the results are empty, clearly say that no data was found.
- Keep the answer concise and clear.
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