"""Register properties.keywords.id as a pgSTAC queryable.

``properties.keywords`` is an array of keyword objects, so pgSTAC's default
path resolution (``content->'properties'->'keywords'->'id'``) yields NULL and
every keyword filter matches nothing.

Register an explicit ``property_path`` that collects the ids of all keywords in
the array, so array operators such as ``a_overlaps`` resolve against a real
text array.

Revision ID: c7b2e5a9d413
Revises: a1f4d7c30e52
Create Date: 2026-09-06

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c7b2e5a9d413"
down_revision: Union[str, None] = "a1f4d7c30e52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

QUERYABLE_NAME = "properties.keywords.id"
PROPERTY_PATH = "jsonb_path_query_array(content, '$.properties.keywords[*].id')"


def upgrade() -> None:
    # pgSTAC's queryables constraint trigger references its own tables
    # unqualified, so pgstac must be on the search_path for the insert.
    op.execute("SET LOCAL search_path TO pgstac, public;")
    op.execute(
        f"""
        INSERT INTO pgstac.queryables
            (name, property_path, property_wrapper, definition)
        SELECT
            '{QUERYABLE_NAME}',
            $path${PROPERTY_PATH}$path$,
            'to_text',
            '{{"type": "array", "items": {{"type": "string"}}}}'::jsonb
        WHERE NOT EXISTS (
            SELECT 1 FROM pgstac.queryables WHERE name = '{QUERYABLE_NAME}'
        );
        """
    )


def downgrade() -> None:
    op.execute(
        f"DELETE FROM pgstac.queryables WHERE name = '{QUERYABLE_NAME}';"
    )
