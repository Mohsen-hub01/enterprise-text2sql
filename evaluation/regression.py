import json
from pathlib import Path


EVALUATION_PATH = Path(__file__).resolve().parent
BASELINE_PATH = EVALUATION_PATH / "baseline" / "baseline.json"

CURRENT_PATH = EVALUATION_PATH / "current_results.json"


MAX_ACCURACY_DROP = 0.05
MAX_LATENCY_INCREASE = 0.25
MAX_RETRY_INCREASE = 0.50


def load_json(path: Path):
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def detect_regressions():
    baseline = load_json(
        BASELINE_PATH
    )

    current = load_json(
        CURRENT_PATH
    )

    regressions = []

    # -------------------------
    # Accuracy
    # -------------------------

    baseline_accuracy = baseline[
        "execution_accuracy"
    ]

    current_accuracy = current[
        "execution_accuracy"
    ]

    minimum_accuracy = (
        baseline_accuracy
        - MAX_ACCURACY_DROP
    )

    if current_accuracy < minimum_accuracy:
        regressions.append(
            {
                "metric": "execution_accuracy",
                "baseline": baseline_accuracy,
                "current": current_accuracy,
                "minimum_allowed": minimum_accuracy,
            }
        )

    # -------------------------
    # Safety
    # -------------------------

    baseline_safety = baseline[
        "safety_rate"
    ]

    current_safety = current[
        "safety_rate"
    ]

    if current_safety < baseline_safety:
        regressions.append(
            {
                "metric": "safety_rate",
                "baseline": baseline_safety,
                "current": current_safety,
            }
        )

    # -------------------------
    # Latency
    # -------------------------

    baseline_latency = baseline[
        "average_latency_seconds"
    ]

    current_latency = current[
        "average_latency_seconds"
    ]

    maximum_latency = (
        baseline_latency
        * (1 + MAX_LATENCY_INCREASE)
    )

    if current_latency > maximum_latency:
        regressions.append(
            {
                "metric": "average_latency_seconds",
                "baseline": baseline_latency,
                "current": current_latency,
                "maximum_allowed": maximum_latency,
            }
        )

    # -------------------------
    # Retries
    # -------------------------

    baseline_retries = baseline[
        "average_retries"
    ]

    current_retries = current[
        "average_retries"
    ]

    if baseline_retries == 0:
        maximum_retries = 0.5
    else:
        maximum_retries = (
            baseline_retries
            * (1 + MAX_RETRY_INCREASE)
        )

    if current_retries > maximum_retries:
        regressions.append(
            {
                "metric": "average_retries",
                "baseline": baseline_retries,
                "current": current_retries,
                "maximum_allowed": maximum_retries,
            }
        )

    # -------------------------
    # Report
    # -------------------------

    print("\n")
    print("=" * 70)
    print("REGRESSION REPORT")
    print("=" * 70)

    print(
        f"Accuracy: "
        f"{baseline_accuracy:.2%}"
        f" -> "
        f"{current_accuracy:.2%}"
    )

    print(
        f"Safety: "
        f"{baseline_safety:.2%}"
        f" -> "
        f"{current_safety:.2%}"
    )

    print(
        f"Latency: "
        f"{baseline_latency:.2f}s"
        f" -> "
        f"{current_latency:.2f}s"
    )

    print(
        f"Retries: "
        f"{baseline_retries:.2f}"
        f" -> "
        f"{current_retries:.2f}"
    )

    print("=" * 70)

    # -------------------------
    # Regression detected
    # -------------------------

    if regressions:
        print(
            "\nREGRESSION DETECTED"
        )

        for regression in regressions:

            print(
                "\nMetric:",
                regression["metric"],
            )

            print(
                "Baseline:",
                regression["baseline"],
            )

            print(
                "Current:",
                regression["current"],
            )

            if (
                "minimum_allowed"
                in regression
            ):
                print(
                    "Minimum allowed:",
                    regression[
                        "minimum_allowed"
                    ],
                )

            if (
                "maximum_allowed"
                in regression
            ):
                print(
                    "Maximum allowed:",
                    regression[
                        "maximum_allowed"
                    ],
                )

        return False

    # -------------------------
    # Everything OK
    # -------------------------

    print(
        "\nNO REGRESSION DETECTED"
    )

    return True


if __name__ == "__main__":
    try:
        success = detect_regressions()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Cannot compare regression results: {exc}")
        print("Run python -m evaluation.run_api_benchmark in Docker first.")
        raise SystemExit(2)

    if not success:
        raise SystemExit(1)
