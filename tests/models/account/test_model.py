from app.models.account.model import *
from app.models.account.scheme import Account
from datetime import datetime


def test_create_account():
    time = datetime.now().replace(microsecond=0)
    address = "abcdefg"
    account = Account(**{"address": address, "created_time": time})

    a = create_account(account)
    assert a["address"] == address
    assert a["created_time"] == time

    account = get_account(address)

    assert account["address"] == address
    assert account["created_time"] == time

    nonce = set_address_nonce(account)
    a = account_collection.find_one({"address": address})
    assert a['nonce'] == nonce

    account_collection.delete_one({"address": address})
    a = account_collection.find_one({"address": address})
    assert a is None

    account = get_account("sdfhlsdfh")
    assert account is None
