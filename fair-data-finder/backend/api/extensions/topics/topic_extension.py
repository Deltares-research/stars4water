"""Topic Extension for STAC FastAPI."""

import logging
from typing import List

from fastapi import APIRouter, Request
from stac_fastapi.types.extension import ApiExtension

from .topic_mapping import get_topic_name

_LOGGER = logging.getLogger(__name__)


class TopicExtension(ApiExtension):
    """Extension to provide topic aggregation endpoint."""

    def __init__(self):
        """Initialize TopicExtension."""
        self.router = APIRouter()
        self.router.add_api_route(
            name="Get Topics",
            path="/topics",
            methods=["GET"],
            endpoint=self.get_topics,
        )

    async def get_topics(self, request: Request):
        """Get aggregated topics with counts.

        Returns:
            dict: JSON response with topics and their counts
        """
        try:
            async with request.app.state.readpool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        topic,
                        COUNT(*) AS count
                    FROM pgstac.items,
                         jsonb_array_elements_text(
                             content -> 'properties' -> 'deltares:topics'
                         ) AS topic
                    GROUP BY topic
                    ORDER BY count DESC
                    LIMIT 1000
                    """
                )

            topics = []
            for row in rows:
                topic_id = row["topic"]
                topics.append(
                    {
                        "id": topic_id,
                        "name": get_topic_name(topic_id),
                        "count": row["count"],
                    }
                )

            return {"topics": topics}

        except Exception as e:
            _LOGGER.error(f"Error retrieving topics: {str(e)}", exc_info=True)
            raise

    def register(self, app):
        """Register the extension with a FastAPI application.

        Args:
            app: The FastAPI application
        """
        app.include_router(self.router, tags=["Topics"])

    @property
    def conformance_classes(self) -> List[str]:
        """Return conformance classes for the extension."""
        return []
