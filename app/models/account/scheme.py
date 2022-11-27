from pydantic import BaseModel
from datetime import datetime


class Account(BaseModel):
    address: str
    created_time: datetime
    nonce: str = ""


class AddressIn(BaseModel):
    address: str


class AddressNonceOut(BaseModel):
    address: str
    nonce: str


class MetamaskLoginIn(BaseModel):
    signature: str
    address: str






