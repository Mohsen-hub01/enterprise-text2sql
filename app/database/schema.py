from sqlalchemy import inspect

from app.database.db import engine


def get_database_schema():
    inspector = inspect(engine)

    schema = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        primary_key = inspector.get_pk_constraint(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)

        schema[table_name] = {
            "columns": [
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                }
                for column in columns
            ],
            "primary_key": primary_key.get(
                "constrained_columns",
                [],
            ),
            "foreign_keys": [
                {
                    "columns": fk.get(
                        "constrained_columns",
                        [],
                    ),
                    "references_table": fk.get(
                        "referred_table"
                    ),
                    "references_columns": fk.get(
                        "referred_columns",
                        [],
                    ),
                }
                for fk in foreign_keys
            ],
        }

    return schema