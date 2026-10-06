from decimal import Decimal

def execute_query(sql: str):
    from app.database.db import execute_query as database_execute_query

    return database_execute_query(sql)


def normalize_value(value):
    if value is None:
        return None

    if isinstance(value, Decimal):
        return round(float(value), 6)

    if isinstance(value, float):
        return round(value, 6)

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def normalize_rows(results: list) -> list:
    """
    Convert database results into tuples of normalized values.
    Column names are intentionally ignored.
    """

    normalized = []

    for row in results:
        normalized_row = tuple(
            normalize_value(value)
            for value in row.values()
        )

        normalized.append(normalized_row)

    return sorted(
        normalized,
        key=repr,
    )


def is_subsequence(
    expected: tuple,
    actual: tuple,
) -> bool:
    """
    Check whether all expected values appear in the actual row
    in the same order.

    Example:

    expected:
        ("Alice", "Martin")

    actual:
        (1, "Alice", "Martin", "alice@example.com", "France")

    => True
    """

    if len(expected) > len(actual):
        return False

    expected_index = 0

    for value in actual:
        if (
            expected_index < len(expected)
            and value == expected[expected_index]
        ):
            expected_index += 1

    return expected_index == len(expected)


def rows_equivalent(
    generated_rows: list,
    reference_rows: list,
) -> bool:
    """
    Two results are considered equivalent when:

    1. They contain the same number of rows.
    2. Every expected/reference row can be found inside
       one generated row.
    3. Extra generated columns are allowed.
    """

    if len(generated_rows) != len(reference_rows):
        return False

    unmatched_generated = list(generated_rows)

    for reference_row in reference_rows:
        match_index = None

        for index, generated_row in enumerate(
            unmatched_generated
        ):
            if is_subsequence(
                reference_row,
                generated_row,
            ):
                match_index = index
                break

        if match_index is None:
            return False

        unmatched_generated.pop(match_index)

    return True


def compare_execution(
    generated_sql: str,
    reference_sql: str,
) -> dict:

    try:
        generated_results = execute_query(
            generated_sql
        )

    except Exception as exc:
        return {
            "correct": False,
            "reason": (
                "Generated SQL execution failed: "
                f"{exc}"
            ),
        }

    try:
        reference_results = execute_query(
            reference_sql
        )

    except Exception as exc:
        return {
            "correct": False,
            "reason": (
                "Reference SQL execution failed: "
                f"{exc}"
            ),
        }

    generated_normalized = normalize_rows(
        generated_results
    )

    reference_normalized = normalize_rows(
        reference_results
    )

    # First: exact result equivalence
    exact_match = (
        generated_normalized
        == reference_normalized
    )

    # Second: allow generated queries to return
    # additional columns as long as the expected
    # values are present.
    projection_match = rows_equivalent(
        generated_normalized,
        reference_normalized,
    )

    correct = (
        exact_match
        or projection_match
    )

    if exact_match:
        reason = "Exact execution result match"

    elif projection_match:
        reason = (
            "Reference result is contained in "
            "the generated result"
        )

    else:
        reason = (
            "Generated and reference results differ"
        )

    return {
        "correct": correct,
        "reason": reason,
        "exact_match": exact_match,
        "projection_match": projection_match,
        "generated_results": generated_results,
        "reference_results": reference_results,
        "generated_normalized": generated_normalized,
        "reference_normalized": reference_normalized,
    }
