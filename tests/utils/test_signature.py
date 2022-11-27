from app.utils.signature import *


def test_verify_signature():
    signature = "0x2196319a38c70015cefcf5623e754636882877b69f40f2cdc9c6e05964a897401fc9897119095979363eedc28c849f71d1051f0ec2e853287e0938a2b83a33351b"
    message = "bEycmTsezYbIvAmebSuPaQZyPcRJutub"
    address = "0x74A7D61E66345eA8cdb85976BEa99640F4c704a2"
    assert verify_signature(signature, message, address)
    assert not verify_signature(signature, message, "adas")


def test_create_nonce():
    assert len(create_nonce()) == 32
    assert create_nonce() != create_nonce()
