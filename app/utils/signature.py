import random
import string
import secrets

from eth_account.messages import encode_defunct
from web3.auto import w3

from app.config import settings


# msg = "I♥SF"
# private_key = b"\xb2\\}\xb3\x1f\xee\xd9\x12''\xbf\t9\xdcv\x9a\x96VK-\xe4\xc4rm\x03[6\xec\xf1\xe5\xb3d"
# message = encode_defunct(text=msg)
# signed_message = w3.eth.account.sign_message(message, private_key=private_key)
# print(signed_message)
# print(private_key)


# def sign_mint_signature(message):
#     message = encode_defunct(text=message)
#     signed_message = w3.eth.account.sign_message(message, private_key=settings.mint_key)
#     return signed_message_to_json(signed_message)
#
#
# def sign_mint_white_list_signature(message):
#     message = encode_defunct(text=message)
#     signed_message = w3.eth.account.sign_message(message, private_key=settings.mint_white_list_key)
#     return signed_message_to_json(signed_message)
#
#
# def signed_message_to_json(signed_message):
#     return {
#         "messageHash": signed_message.messageHash.hex(),
#         "v": signed_message.v,
#         "r": signed_message.r,
#         "s": signed_message.s,
#         "signature": signed_message.signature.hex()
#     }


def verify_signature(signature: str, message: str, address: str) -> bool:
    message = encode_defunct(text=message)
    return address.lower() == w3.eth.account.recover_message(message, signature=signature).lower()


def create_nonce():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


# if __name__ == "__main__":
#     hex_signature = '0xf1fcf7b5d152e1d96f69955fcf7a999acc276ea116272bfe135351dc19f1c9472852205e2863b306cd488379e6af014bd213fb0f279ab44651b2e53dda89de2b1b'
#     msg = "Sign for address nonce: mnDWMKQlxqtHMwoTBfDPkpqXYGzRHYcN"
#
#     print("0x78552ff5ce2a52d26857786548891b01da29b929")
#     print(verify_signature(hex_signature, msg, "0x78552ff5ce2a52d26857786548891b01da29b929"))
#     # print(create_nonce())

# res = w3.eth.sign(
#       '0xd3CdA913deB6f67967B99D67aCDFa1712C293601',
#       text='some-text-tö-sign')
# 
# print(res)
#
# from web3 import Web3
# from eth_account.messages import encode_defunct, _hash_eip191_message
#
# msg = "abc123"
# Web3.toHex(text=msg)
# # hex_message = '0x49e299a55346'
# hex_message = Web3.toHex(text=msg)
# # hex_signature = '0xe6ca9bba58c88611fad66a6ce8f996908195593807c4b38bd528d2cff09d4eb33e5bfbbf4d3e39b1a2fd816a7680c19ebebaf3a141b239934ad43cb33fcec8ce1c'
# hex_signature = '0x5df54d97eea8edd3ac6c65d18c400aacc2e1e1dae953e3f808cea02461534d427c2d0379b124d2736f7a480619ccf17e10db52bd78cd83fe56b5861a82825e6e1b'
#
# message = encode_defunct(text=msg)
# print(w3.eth.account.recover_message(message, signature=hex_signature))
#
#
# # ecrecover in Solidity expects an encoded version of the message
#
# # - encode the message
# message = encode_defunct(hexstr=hex_message)
#
# # - hash the message explicitly
# message_hash = _hash_eip191_message(message)
#
# # Remix / web3.js expect the message hash to be encoded to a hex string
# hex_message_hash = Web3.toHex(message_hash)
#
# # ecrecover in Solidity expects the signature to be split into v as a uint8,
# #   and r, s as a bytes32
# # Remix / web3.js expect r and s to be encoded to hex
# sig = Web3.toBytes(hexstr=hex_signature)
# v, hex_r, hex_s = Web3.toInt(sig[-1]), Web3.toHex(sig[:32]), Web3.toHex(sig[32:64])
#
# # ecrecover in Solidity takes the arguments in order = (msghash, v, r, s)
# ec_recover_args = (hex_message_hash, v, hex_r, hex_s)
# print(ec_recover_args)
# # ('0x1476abb745d423bf09273f1afd887d951181d25adc66c4834a70491911b7f750',
# #  28,
# #  '0xe6ca9bba58c88611fad66a6ce8f996908195593807c4b38bd528d2cff09d4eb3',
# #  '0x3e5bfbbf4d3e39b1a2fd816a7680c19ebebaf3a141b239934ad43cb33fcec8ce')
#
# print(w3.eth.account.recover_message(message, vrs=(v, hex_r, hex_s)))


# 0x74A7D61E66345eA8cdb85976BEa99640F4c704a2
