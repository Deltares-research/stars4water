from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from api.core.stacdms import StacDmsApi
from api.extensions.core.sso_auth_extension import SSOAuthExtension
from api.extensions.topics.topic_extension import TopicExtension
from api.extensions.topics.topic_mapping import TOPIC_NAMES, get_topic_name
from fastapi import FastAPI
from fastapi_sso import MicrosoftSSO
from httpx import ASGITransport, AsyncClient
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.extensions.core import SearchFilterExtension
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.pgstac.extensions.filter import FiltersClient
from stac_fastapi.types.config import Settings


def test_get_topic_name_known_code():
    """Known ISO 19115 TopicCategory codes map to their human-readable name."""
    assert get_topic_name("geoscientificInformation") == "Geoscientific Information"


def test_get_topic_name_custom_value():
    """Custom (non-ISO) topic values also have a mapped display name."""
    assert get_topic_name("Water quality") == "Water Quality"


def test_get_topic_name_unknown_falls_back_to_id():
    """Unmapped topic ids fall back to being returned unchanged."""
    assert get_topic_name("not_a_real_topic") not in TOPIC_NAMES.values()
    assert get_topic_name("not_a_real_topic") == "not_a_real_topic"


class _FakeRow(dict):
    """Mimics an asyncpg.Record's mapping-style access used by the endpoint."""


class _FakeAggregationConnection:
    def __init__(self, rows):
        self._rows = rows

    async def fetch(self, *_args, **_kwargs):
        return self._rows


class _FakeAggregationPool:
    def __init__(self, rows):
        self._rows = rows

    @asynccontextmanager
    async def acquire(self):
        yield _FakeAggregationConnection(self._rows)


@pytest_asyncio.fixture(scope="function")
async def topics_app():
    """Minimal app exposing only the TopicExtension, with login disabled.

    Built directly (instead of reusing the shared ``app`` fixture) so these
    tests don't depend on the JWT cookie flow used by ``authenticated_client``.
    """
    settings = Settings.get()
    search_filter_extension = SearchFilterExtension(client=FiltersClient())
    extensions = [search_filter_extension, TopicExtension()]
    post_request_model = create_post_request_model(extensions)
    stac_dms_api = StacDmsApi(
        settings=settings,
        client=CoreCrudClient(pgstac_search_model=post_request_model),
        extensions=extensions,
        middlewares=[],
        search_get_request_model=create_get_request_model(extensions),
        search_post_request_model=post_request_model,
    )
    SSOAuthExtension(
        settings=settings,
        sso_client=MicrosoftSSO(client_id="", client_secret=""),
        login_enabled=False,
        public_endpoints=[{"path": "/topics", "method": "GET"}],
    ).register(stac_dms_api.app)
    yield stac_dms_api.app


@pytest_asyncio.fixture(scope="function")
async def topics_client(topics_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=topics_app), base_url="http://test-server"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_get_topics_aggregates_and_maps_names(
    topics_app: FastAPI, topics_client: AsyncClient
):
    """GET /topics returns each topic with its count and mapped display name."""
    fake_rows = [
        _FakeRow(topic="farming", count=3),
        _FakeRow(topic="not_a_real_topic", count=1),
    ]
    topics_app.state.readpool = _FakeAggregationPool(fake_rows)

    response = await topics_client.get("/topics")

    assert response.status_code == 200
    assert response.json() == {
        "topics": [
            {"id": "farming", "name": "Farming", "count": 3},
            {"id": "not_a_real_topic", "name": "not_a_real_topic", "count": 1},
        ]
    }


@pytest.mark.asyncio
async def test_get_topics_empty_when_no_data(
    topics_app: FastAPI, topics_client: AsyncClient
):
    """GET /topics returns an empty list when no items carry deltares:topics."""
    topics_app.state.readpool = _FakeAggregationPool([])

    response = await topics_client.get("/topics")

    assert response.status_code == 200
    assert response.json() == {"topics": []}
