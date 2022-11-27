from datetime import datetime
from fastapi import APIRouter, HTTPException, Response, status, Depends
from app.models.account.scheme import AddressIn, AddressNonceOut, MetamaskLoginIn
from app.models.account.model import *
from app.utils.jwt_token import create_access_token, verify_jwt
from app.utils.signature import verify_signature

router = APIRouter(
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get('/address/nonce/{address}', response_model=AddressNonceOut)
def get_address_nonce(address: str):
    account = get_account(address)
    if not account:
        # create account
        account = Account(**{"address": address.lower(), "created_time": datetime.now()})
        account = create_account(account)

    nonce = set_address_nonce(account)
    return {"address": address, "nonce": nonce}


@router.post('/address/authentication')
def metamask_login(verify_data: MetamaskLoginIn):
    account = get_account(verify_data.address)
    if not account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No this address.")
    message = "Sign for address nonce: " + account.get('nonce')
    if not verify_signature(verify_data.signature, message, verify_data.address):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature.")

    set_address_nonce(account)  # update new nonce

    access_token = create_access_token(verify_data.address)
    return {"access_token": access_token}


@router.post("/address/validate")
def validate_token(address: AddressIn, payload=Depends(verify_jwt)):
    if address.address != payload['sub']:
        raise HTTPException(status_code=401, detail="Invalid.")
    return ""


