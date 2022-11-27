from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def setup_module():
    # Do something
    ...


def test_main():
    res = client.get('/ping')
    assert res.status_code == 200
    assert res.text == '"is ok"'


def test_time():
    res = client.get('time')
    assert res.status_code == 200


def test_docs():
    res = client.get('docs')
    assert res.status_code == 404
