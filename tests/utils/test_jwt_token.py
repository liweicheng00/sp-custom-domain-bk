import base64
import pytest
from app.utils.jwt_token import *
from fastapi.security import HTTPAuthorizationCredentials
import json


def test_create_access_token():
    identity = "abcdefg"
    access_token = create_access_token(identity)
    token = HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token)

    header, payload, signature = access_token.split('.')
    header = json.loads(base64.b64decode(header).decode('utf-8'))
    assert token
    assert header['typ'] == "JWT"
    assert header['alg'] == "HS256"


def test_verify_jwt():
    identity = "abcdefg"
    access_token = create_access_token(identity)
    token = HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token)
    res = verify_jwt(token)
    assert res['sub'] == 'abcdefg'

    expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhYmNkZWZnIiwiZXhwIjoxNjUwMDA0NzY5LCJpYXQiOjE2NTAwMDUzNjksImF1ZCI6Im8ybWV0YS5pbyIsImlzcyI6Im8ybWV0YS5pbyJ9.EJD0r5CdeKUyQXK4Gpa_ynyx8XyuatiWgdu8cS_O6Zs"
    with pytest.raises(HTTPException):
        verify_jwt(expired_token)
