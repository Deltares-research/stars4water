"""Make pgstac.to_text(text) decode JSON literals so CQL2 ``like`` matches.

Revision ``f8a3c5e92b01`` added a ``pgstac.to_text(text)`` overload to keep
PostgreSQL from raising AmbiguousFunctionError when resolving an untyped
string literal against ``to_text(jsonb)`` and ``to_text(geometry)``.

That overload returned its argument verbatim, which silently broke every text
search.  pgSTAC renders a CQL2 ``like`` as::

    to_text(content->'properties'->'title') LIKE to_text('"%water%"')

The right-hand literal is the *JSON encoding* of the pattern, so returning it
verbatim compares against ``"%water%"`` including the double quotes and never
matches a stored title.

Decode the literal as JSON, mirroring ``to_text(jsonb)`` semantics, and fall
back to the raw string when it is not valid JSON.  Both earlier fixes keep
working: the overload still resolves the ambiguity, and ``to_text(geometry)``
still backs ``isNull(geometry)``.

Revision ID: a1f4d7c30e52
Revises: f8a3c5e92b01
Create Date: 2026-09-06

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1f4d7c30e52"
down_revision: Union[str, None] = "f8a3c5e92b01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION pgstac.to_text(text)
            RETURNS text
            LANGUAGE plpgsql
            IMMUTABLE PARALLEL SAFE STRICT
        AS $f$
        DECLARE
            parsed jsonb;
        BEGIN
            BEGIN
                parsed := $1::jsonb;
            EXCEPTION
                WHEN others THEN
                    -- Not a JSON literal; use the value as given.
                    RETURN $1;
            END;
            RETURN CASE
                WHEN jsonb_typeof(parsed) IN ('array', 'object') THEN parsed::text
                ELSE parsed->>0
            END;
        END;
        $f$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION pgstac.to_text(text)
            RETURNS text
            LANGUAGE sql
            IMMUTABLE PARALLEL SAFE STRICT
        AS $f$ SELECT $1 $f$;
        """
    )
