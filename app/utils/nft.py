import time
from app.exception_handler import GetOwnerError
from web3 import Web3
from web3.exceptions import ContractLogicError
from app.config import settings
import asyncio
import random
from requests import HTTPError

w3 = Web3(Web3.HTTPProvider(settings.web3_url + settings.alchemy_token_key))
abi = {
    "staging": "",
    "test": "",
    "demo": "",
    "hotfix": "",
    "rc": "",
    "production": ""
}
contract_instance = w3.eth.contract(address=settings.contract_address, abi=abi[settings.runtime_env])


def get_nft_owner(token: int):
    return contract_instance.functions.ownerOf(token).call().lower()


async def check_nft_owner(token_id: list, address: str):
    try:
        owner_address = await get_owner_of_tokens(token_id)
        return all([addr.lower() == address.lower() for addr in owner_address])
    except ContractLogicError:
        return False


async def get_owner_of_tokens(tokens):
    loop = asyncio.get_event_loop()
    if len([task for task in asyncio.all_tasks() if not task.done()]) > 500:
        raise

    tasks = []
    for i in tokens:
        tasks.append(loop.run_in_executor(None, get_owner, int(i)))
    try:
        return await asyncio.gather(*tasks)
    except GetOwnerError:
        raise


def get_owner(token: int, times=0):
    try:
        if times > 5:
            raise GetOwnerError
        times += 1
        return contract_instance.functions.ownerOf(token).call()
    except HTTPError as e:
        if e.response.status_code == 429:
            print('sleep a little', token)
            sleep = random.randrange(1000, 1250, 1)
            time.sleep(sleep / 1000)
            print('wake up after', sleep, token)
            get_owner(token, times)
