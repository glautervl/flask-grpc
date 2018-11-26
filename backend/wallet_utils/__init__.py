import hashlib
from mnemonic import Mnemonic
from pycoin.key.BIP32Node import BIP32Node
import ecdsa
from web3 import Web3, HTTPProvider


def create_wallet(mnemonic, index):
    w3 = Web3(HTTPProvider("https://kovan.infura.io"))
    master_key = BIP32Node.from_master_secret(Mnemonic("english").to_seed(mnemonic))
    purpose_subtree = master_key.subkey(i=44, is_hardened=True)
    coin_type_subtree = purpose_subtree.subkey(i=60, is_hardened=True)
    account_subtree = coin_type_subtree.subkey(i=0, is_hardened=True)
    change_subtree = account_subtree.subkey(i=0)
    account = change_subtree.subkey(i=index)
    private_key = account.secret_exponent().to_bytes(32, 'big')
    public_key = ecdsa.SigningKey.from_string(string=private_key,
                                              curve=ecdsa.SECP256k1,
                                              hashfunc=hashlib.sha256).get_verifying_key()
    address = w3.toChecksumAddress("0x" + w3.sha3(hexstr=public_key.to_string().hex())[12:].hex())
    return {
        "address": address,
        "private_key": private_key.hex()
    }


def get_wallet(mnemonic, index):
    response = None
    try:
        response = create_wallet(mnemonic, index)
    except Exception as e:
        print(e)
    return response
