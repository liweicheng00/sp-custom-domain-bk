from app.setup import *


def test_create_account_collection():
    col = db.list_collection_names()
    assert 'account' in col

