import web3
import json
import hashlib
from configparser import ConfigParser, ExtendedInterpolation

from snet_cli.commands import BlockchainCommand

from registry_utils import get_registry_info
from service_utils import call, call_daemon

conf = ConfigParser(interpolation=ExtendedInterpolation(), delimiters=("=",))


class CustomArgs:
    def __init__(self):
        self.organization_name = ""
        self.service_name = ""
        self.agent_address = ""
        self.agent_at = ""
        self.max_price = 1000000000
        self.yes = True


def type_converter(t):
    if t.endswith("[]"):
        return lambda x: list(map(type_converter(t.replace("[]", "")), json.loads(x)))
    else:
        if "int" in t:
            return lambda x: web3.Web3.toInt(text=x)
        elif "bytes32" in t:
            return lambda x: web3.Web3.toBytes(text=x).ljust(32, b"\0") if not x.startswith("0x") else web3.Web3.toBytes(hexstr=x).ljust(32, b"\0")
        elif "byte" in t:
            return lambda x: web3.Web3.toBytes(text=x) if not x.startswith("0x") else web3.Web3.toBytes(hexstr=x)
        elif "address" in t:
            return web3.Web3.toChecksumAddress
        else:
            return str


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


def insert_package(spec_dir, spec_hash):
    for proto_file in spec_dir.glob("**/*.proto"):
        new_hash = "{}{}".format(spec_hash, str(proto_file).split("/")[-1])
        new_hash = new_hash.encode("utf-8")
        pkg_hash = hashlib.sha256(new_hash)
        pkg_hash = "snet_" + pkg_hash.hexdigest()

        with open(str(proto_file), 'r') as f:
            filelines = f.readlines()

        flag_insert = False
        idx_insert = 1
        for idx_file, line in enumerate(filelines[:]):
            if "package " in line:
                filelines[idx_file] = "package {};\n".format(pkg_hash)
                flag_insert = False
            if "syntax = " in line:
                flag_insert = True
                if filelines[idx_file + 1] == "\n":
                    idx_insert = idx_file + 1
        if flag_insert:
            filelines[idx_insert] = "\npackage {};\n\n".format(pkg_hash)

        with open(str(proto_file), 'w') as f:
            f.writelines(filelines)


def main():
    args = CustomArgs()
    get_conf()
    iblockchain = BlockchainCommand(conf, args)
    organizations_json = get_registry_info(iblockchain)
    i = 1
    org_list = []
    for org, info in organizations_json.items():
        org_list.append(org)
        print("{}: {}".format(i, org))
        i += 1

    org_idx = int(input("Organization: "))
    if org_idx < len(org_list):
        i = 1
        service_list = []
        org_info = organizations_json[org_list[org_idx-1]]
        for service, info in org_info.items():
            service_list.append(service)
            print("{}: {}".format(i, service))
            i += 1
        service_idx = int(input("Service: "))
        if service_idx < len(service_list):
            srv_info = org_info[service_list[service_idx - 1]]
            print(json.dumps(srv_info, indent=4))
            method = input("Method: ")
            params = input("Params: ")
            if input("Blockchain? ") == "y":
                iblockchain.args.agent_at = srv_info["agent_address"]
                iblockchain.args.method = method
                iblockchain.args.params = params
                response = call_daemon(iblockchain)
                print(response.getvalue().strip())
            else:
                proto_hash = srv_info["metadata_uri"]
                spec_hash = str(proto_hash).split("/")[-1]
                print(call(iblockchain, spec_hash, method, params))


if __name__ == "__main__":
    main()
