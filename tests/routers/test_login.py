from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.utils.jwt_token import create_access_token

client = TestClient(app, base_url="http://www.o2meta.io")


def test_get_address_nonce():
    address = "a"*32
    res = client.get(f'/address/nonce/{address}')
    assert res.status_code == 200


def test_metamask_login():
    # Address not exists
    address = "0x0000"
    signature = "0x2aa9d80f64225dbb4cb52d7bbdd0e278a41ff59f08be651f0f377e209d86921c19127808800046c37a5f747787ca71695761dc40515bca73a1f75fd7707cf2171b"

    res = client.post('/address/authentication', json={"signature": signature, "address": address})
    assert res.status_code == 400


def test_validate_token():
    address = "a"*32
    jwt = create_access_token(address)

    res = client.post(f'/address/validate', json={'address': address}, headers={"Authorization": f'bearer {jwt}'})
    assert res.status_code == 200

    res = client.post('/address/validate', json={'address': "address"}, headers={"Authorization": f'bearer {jwt}'})
    assert res.status_code == 401

    res = client.post('/address/validate', json={'address': address})
    assert res.status_code == 403

