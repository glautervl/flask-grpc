import sys
from pathlib import Path
from io import StringIO
from configparser import ConfigParser, ExtendedInterpolation

from snet_cli.commands import BlockchainCommand

from registry_utils import get_registry_info


conf = ConfigParser(interpolation=ExtendedInterpolation(), delimiters=("=",))


class CustomArgs:
    def __init__(self):
        self.organization_name = ""
        self.service_name = ""
        self.agent_address = ""
        self.agent_at = ""
        self.max_price = 1000000000
        self.yes = True


def persist():
    with open("./config", "w") as f:
        conf.write(f)


def get_conf():
    global conf
    try:
        with open("./config", "r") as f:
            conf.read_file(f)
    except Exception as e:
        print(e)
        conf = {
            "network.kovan": {"default_eth_rpc_endpoint": "https://kovan.infura.io"},
            "network.mainnet": {"default_eth_rpc_endpoint": "https://mainnet.infura.io"},
            "network.ropsten": {"default_eth_rpc_endpoint": "https://ropsten.infura.io"},
            "network.rinkeby": {"default_eth_rpc_endpoint": "https://rinkeby.infura.io"},
            "ipfs": {"default_ipfs_endpoint": "http://ipfs.singularitynet.io:80"},
            "session": {
                "init": "1",
                "default_gas_price": "1000000000",
                "default_wallet_index": "0",
                "default_eth_rpc_endpoint": "https://kovan.infura.io"
            },
        }
    conf.persist = persist
    return conf


def main():
    args = CustomArgs()
    get_conf()
    iblockchain = BlockchainCommand(conf, args)
    out_f = StringIO()
    get_registry_info(iblockchain, out_f)


if __name__ == "__main__":
    main()