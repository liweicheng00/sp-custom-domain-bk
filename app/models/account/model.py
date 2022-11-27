from app.models.database import db
from app.models.account.scheme import Account
from app.utils.signature import create_nonce

account_collection = db['account']


def get_account(address: str):
    account = account_collection.find_one({"address": address})
    return account


def create_account(account: Account) -> dict:

    res = account_collection.insert_one(account.dict())
    account = account_collection.find_one({"_id": res.inserted_id})
    return account


def set_address_nonce(account: dict) -> str:
    nonce = create_nonce()
    account_collection.update_one({"address": account['address']}, {"$set": {"nonce": nonce}})
    return nonce
