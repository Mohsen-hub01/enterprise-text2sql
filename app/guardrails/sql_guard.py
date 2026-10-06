from sqlglot import parse_one, exp
from sqlglot.errors import ParseError


ALLOWED_TABLES = {
    "customers",
    "products",
    "orders",
    "order_items",
}


def validate_sql(sql: str) -> dict:
    cleaned_sql = sql.strip()

    if not cleaned_sql:
        return {
            "valid": False,
            "reason": "Empty SQL query",
        }

    try:
        tree = parse_one(
            cleaned_sql,
            dialect="postgres",
        )

    except ParseError as exc:
        return {
            "valid": False,
            "reason": f"Invalid SQL syntax: {exc}",
        }

    # Only SELECT queries
    if not isinstance(tree, exp.Select):
        return {
            "valid": False,
            "reason": "Only SELECT queries are allowed",
        }

    # Extract all referenced tables
    tables = {
        table.name.lower()
        for table in tree.find_all(exp.Table)
    }

    unauthorized_tables = tables - ALLOWED_TABLES

    if unauthorized_tables:
        return {
            "valid": False,
            "reason": (
                "Unauthorized table(s): "
                + ", ".join(sorted(unauthorized_tables))
            ),
        }

    return {
        "valid": True,
        "reason": "Query passed SQL AST validation",
        "tables": sorted(tables),
    }


def apply_limit(sql: str, limit: int = 100) -> str:
    tree = parse_one(
        sql,
        dialect="postgres",
    )

    # Add LIMIT only if the query does not already have one
    if tree.args.get("limit") is None:
        tree = tree.limit(limit)

    return tree.sql(
        dialect="postgres",
    )