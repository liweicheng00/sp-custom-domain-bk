from fastapi.testclient import TestClient
from app.main import app
from app.utils.jwt_token import create_access_token

client = TestClient(app)


def test_update_metadata_logo(monkeypatch, client_with_startup):
    address = "a" * 32
    jwt = create_access_token(address)

    with open('tests/assets/test.png', "rb") as f:
        res = client_with_startup.post(f'/metadata/logo',
                                       data={"id": "abc"},
                                       files={"file": ("filename", f, "image/jpeg")}
                                       , headers={"Authorization": f'bearer {jwt}'})

    assert res.status_code == 200
    assert res.json()['image_url'] == 'https://url.com'
