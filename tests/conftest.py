import functools
import pytest
from starlette.testclient import TestClient
from app.models.database import connection
from app.setup import *
import asyncio


@pytest.fixture(scope="module", autouse=True)
def tests_setup_and_teardown():
    create_account_collection()
    yield

    connection.drop_database('test')


@pytest.fixture(scope="module")
def client_with_startup():
    from app.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    res = policy.new_event_loop()
    asyncio.set_event_loop(res)
    res._close = res.close
    res.close = lambda: None
    # assert 0

    yield res

    res._close()

@pytest.fixture
def test_client_factory(anyio_backend_name, anyio_backend_options):
    # anyio_backend_name defined by:
    # https://anyio.readthedocs.io/en/stable/testing.html#specifying-the-backends-to-run-on
    if anyio_backend_name == "trio":
        pytest.skip("Trio not supported (yet!)")
    return functools.partial(
        TestClient,
        backend=anyio_backend_name,
        backend_options=anyio_backend_options,
    )
