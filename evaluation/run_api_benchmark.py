import json
import time
from pathlib import Path

import requests

from evaluation.evaluators.execution_accuracy import (
    compare_execution,
)


API_URL = "http://127.0.0.1:8000/query"

DATASET_PATH = Path(
    "evaluation/datasets/text2sql_eval.json"
)

CURRENT_RESULTS_PATH = Path(
    "evaluation/current_results.json"
)


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
    safe = 0

    latencies = []
    retry_counts = []

    evaluations = []

    for example in dataset:
        question = example["question"]

        print("\n" + "=" * 80)
        print(
            f"Testing {example['id']}: "
            f"{question}"
        )
        print("=" * 80)

        start = time.perf_counter()

        try:
            response = requests.post(
                API_URL,
                json={
                    "question": question
                },
                timeout=60,
            )

        except requests.RequestException as exc:
            latency = (
                time.perf_counter()
                - start
            )

            latencies.append(latency)

            print("\nAPI REQUEST ERROR")
            print(f"Error: {exc}")
            print(
                f"Latency: "
                f"{latency:.2f}s"
            )

            evaluations.append(
                {
                    "id": example["id"],
                    "question": question,
                    "category": example.get(
                        "category"
                    ),
                    "correct": False,
                    "latency": latency,
                    "error": str(exc),
                }
            )

            continue

        latency = (
            time.perf_counter()
            - start
        )

        latencies.append(latency)

        if response.status_code != 200:
            print("\nAPI ERROR")

            print(
                f"Status code: "
                f"{response.status_code}"
            )

            print(response.text)

            evaluations.append(
                {
                    "id": example["id"],
                    "question": question,
                    "category": example.get(
                        "category"
                    ),
                    "correct": False,
                    "latency": latency,
                    "error": response.text,
                }
            )

            continue

        agent_result = response.json()

        generated_sql = agent_result.get(
            "safe_sql"
        )

        if not generated_sql:
            generated_sql = (
                agent_result.get(
                    "generated_sql"
                )
            )

        validation = agent_result.get(
            "validation",
            {},
        )

        retry_count = agent_result.get(
            "retry_count",
            0,
        )

        retry_counts.append(
            retry_count
        )

        if validation.get("valid"):
            safe += 1

        if not generated_sql:
            evaluation = {
                "correct": False,
                "reason": (
                    agent_result.get(
                        "error"
                    )
                    or
                    "No SQL was generated or executed"
                ),
            }

        else:
            evaluation = compare_execution(
                generated_sql=generated_sql,
                reference_sql=example[
                    "reference_sql"
                ],
            )

        is_correct = evaluation.get(
            "correct",
            False,
        )

        if is_correct:
            correct += 1

        status = (
            "PASS"
            if is_correct
            else "FAIL"
        )

        print(
            f"\nStatus: {status}"
        )

        print("\nQuestion:")
        print(question)

        print("\nGenerated SQL:")
        print(
            generated_sql
            if generated_sql
            else "None"
        )

        print("\nReference SQL:")
        print(
            example["reference_sql"]
        )

        if not is_correct:
            print(
                "\nFAILURE DETAILS"
            )

            print(
                "\nGenerated result:"
            )

            print(
                evaluation.get(
                    "generated_normalized",
                    evaluation.get(
                        "generated_results"
                    ),
                )
            )

            print(
                "\nReference result:"
            )

            print(
                evaluation.get(
                    "reference_normalized",
                    evaluation.get(
                        "reference_results"
                    ),
                )
            )

            print(
                "\nReason:"
            )

            print(
                evaluation.get(
                    "reason",
                    "Generated and reference results differ",
                )
            )

        else:
            print(
                "\nResult comparison:"
            )

            print(
                "Generated result matches reference result."
            )

        print("\nValidation:")
        print(validation)

        print(
            f"\nLatency: "
            f"{latency:.2f}s"
        )

        print(
            f"Retries: "
            f"{retry_count}"
        )

        evaluations.append(
            {
                "id": example["id"],
                "question": question,
                "category": example.get(
                    "category"
                ),
                "generated_sql": generated_sql,
                "reference_sql": example[
                    "reference_sql"
                ],
                "correct": is_correct,
                "latency": latency,
                "retry_count": retry_count,
                "validation": validation,
                "details": evaluation,
            }
        )

    execution_accuracy = (
        correct / total
        if total
        else 0
    )

    safety_rate = (
        safe / total
        if total
        else 0
    )

    average_latency = (
        sum(latencies)
        / len(latencies)
        if latencies
        else 0
    )

    average_retries = (
        sum(retry_counts)
        / len(retry_counts)
        if retry_counts
        else 0
    )

    results = {
        "total": total,
        "correct": correct,
        "execution_accuracy": execution_accuracy,
        "safety_rate": safety_rate,
        "average_latency_seconds": average_latency,
        "average_retries": average_retries,
        "evaluations": evaluations,
    }

    print(
        "\n\n"
        + "=" * 80
    )

    print(
        "BENCHMARK RESULTS"
    )

    print(
        "=" * 80
    )

    print(
        f"Correct: "
        f"{correct}/{total}"
    )

    print(
        f"Execution accuracy: "
        f"{execution_accuracy:.2%}"
    )

    print(
        f"Safety rate: "
        f"{safety_rate:.2%}"
    )

    print(
        f"Average latency: "
        f"{average_latency:.2f}s"
    )

    print(
        f"Average retries: "
        f"{average_retries:.2f}"
    )

    print(
        "=" * 80
    )

    with open(
        CURRENT_RESULTS_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
            default=str,
)

    print(
        f"\nCurrent results saved to "
        f"{CURRENT_RESULTS_PATH}"
    )

    return results


if __name__ == "__main__":
    run_benchmark()