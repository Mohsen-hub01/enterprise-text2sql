import json
from pathlib import Path

from app.agent.graph import text2sql_graph
from evaluation.evaluators.execution_accuracy import (
    compare_execution,
)


DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "text2sql_eval.json"


def load_dataset():
    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def run_benchmark():
    dataset = load_dataset()

    total = len(dataset)
    correct = 0

    evaluations = []

    for example in dataset:
        question = example["question"]

        print(
            f"\nTesting {example['id']}: "
            f"{question}"
        )

        agent_result = text2sql_graph.invoke(
            {
                "question": question,
                "retry_count": 0,
            }
        )

        generated_sql = agent_result.get(
            "safe_sql"
        )

        if not generated_sql:
            evaluation = {
                "correct": False,
                "reason": (
                    agent_result.get("error")
                    or "No SQL was executed"
                ),
            }

        else:
            evaluation = compare_execution(
                generated_sql=generated_sql,
                reference_sql=example[
                    "reference_sql"
                ],
            )

        if evaluation["correct"]:
            correct += 1

        evaluations.append(
            {
                "id": example["id"],
                "question": question,
                "category": example["category"],
                "generated_sql": generated_sql,
                "reference_sql": example[
                    "reference_sql"
                ],
                "correct": evaluation["correct"],
                "details": evaluation,
            }
        )

        status = (
            "PASS"
            if evaluation["correct"]
            else "FAIL"
        )

        print(status)

        if generated_sql:
            print(
                "Generated:",
                generated_sql,
            )

    accuracy = (
        correct / total
        if total
        else 0
    )

    print("\n----------------")
    print("BENCHMARK RESULTS")
    print("----------------")

    print(
        f"Correct: {correct}/{total}"
    )

    print(
        f"Execution accuracy: "
        f"{accuracy:.2%}"
    )

    return {
        "total": total,
        "correct": correct,
        "execution_accuracy": accuracy,
        "evaluations": evaluations,
    }


if __name__ == "__main__":
    run_benchmark()
