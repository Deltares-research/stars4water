"""Register properties.deltares:topics as a pgSTAC queryable.

Topics are stored as a JSON array. Registering an explicit path and array
definition lets pgSTAC resolve CQL2 array operators against its text values.

Revision ID: d2f8e5c1a906
Revises: c7b2e5a9d413
Create Date: 2026-09-07

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d2f8e5c1a906"
down_revision: Union[str, None] = "c7b2e5a9d413"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

QUERYABLE_NAME = "properties.deltares:topics"
PROPERTY_PATH = 'jsonb_path_query_array(content, \'$.properties."deltares:topics"[*]\')'


def upgrade() -> None:
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
