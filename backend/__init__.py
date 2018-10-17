import os
import sys
import time
import subprocess
import web3
import json
import hashlib
from pathlib import Path
from configparser import ConfigParser, ExtendedInterpolation

from snet_cli.utils import get_web3, get_agent_version
from snet_cli.commands import BlockchainCommand

from service_utils import call, call_daemon_static


conf = ConfigParser(interpolation=ExtendedInterpolation(), delimiters=("=",))
backend_path = Path(__file__).absolute().parent


class MemSingleton:
    def __init__(self):
        self.registry_folder = backend_path.joinpath("registry")
        self.registry_cli = "registry_cli.py"
        self.services_json_file = ""
        self.organizations_dict = {}
        self.keep_running = False

        # Job Invocation
        self.endpoint = ""
        self.spec_hash = ""
        self.user_account = "MetaMask is not enabled!"
        self.agent_address = ""
        self.job_address = ""
        self.job_price = 0
        self.job_signature = ""

        # Transactions variables
        self.receipt = {}
        self.events = {}


mem = MemSingleton()


class CustomArgs:
    def __init__(self):
        self.key = None
        self.value = None
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
    conf_path = backend_path.joinpath("config")
    with open(conf_path, "w") as f:
        conf.write(f)


def get_conf():
    global conf
    try:
        conf_path = backend_path.joinpath("config")
        with open(conf_path, "r") as f:
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


def start_registry_cli():
    while mem.keep_running:
        print("Updating with registry-cli...")
        p = subprocess.Popen([sys.executable, mem.registry_cli], cwd=backend_path)
        p.wait()
        time.sleep(5)


def update_organization_dict():
    if not os.path.exists(mem.registry_folder):
        os.makedirs(mem.registry_folder)

    print("Getting JSON...")
    found = False
    for file in os.listdir(mem.registry_folder):
        filepath = mem.registry_folder.joinpath(file)
        if ".json" in file:
            if file != mem.services_json_file:
                if mem.services_json_file != "":
                    delete_filepath = mem.registry_folder.joinpath(mem.services_json_file)
                    print("delete_filepath: ", delete_filepath)
                    # os.remove(delete_filepath)
                with open(filepath) as f:
                    mem.organizations_dict = json.load(f)
                    mem.services_json_file = file
            found = True
            break
    return found


def call_api(job_address, job_signature, endpoint, spec_hash, method, params):
    response = call(job_address, job_signature, endpoint, spec_hash, method, params)
    return response


def call_service_static(agent_address, method, params):
    args = CustomArgs()
    get_conf()
    iblockchain = BlockchainCommand(conf, args)
    iblockchain.args.agent_at = agent_address
    iblockchain.args.method = method
    iblockchain.args.params = params
    response = call_daemon_static(iblockchain)
    return response.getvalue().strip()


def get_agent_ver(agent_address):
    w3 = get_web3("https://kovan.infura.io")
    return get_agent_version(w3, agent_address)


def main():
    while True:
        args = CustomArgs()
        get_conf()
        iblockchain = BlockchainCommand(conf, args)
        start_registry_cli()

        update_organization_dict()

        i = 1
        org_list = []
        for org, info in mem.organizations_dict.items():
            org_list.append(org)
            print("{}: {}".format(i, org))
            i += 1

        org_idx = int(input("Organization: ")) - 1
        if org_idx < len(org_list):
            i = 1
            service_list = []
            org_info = mem.organizations_dict[org_list[org_idx]]
            for service, info in org_info.items():
                service_list.append(service)
                print("{}: {}".format(i, service))
                i += 1
            service_idx = int(input("Service: ")) - 1
            if service_idx < len(service_list):
                srv_info = org_info[service_list[service_idx]]
                print(json.dumps(srv_info, indent=4))
                method = input("Method: ")
                params = input("Params: ")
                if input("Blockchain? ") == "y":
                    iblockchain.args.agent_at = srv_info["agent_address"]
                    iblockchain.args.method = method
                    iblockchain.args.params = params
                    response = call_daemon_static(iblockchain)
                    print(response.getvalue().strip())
                else:
                    proto_hash = srv_info["metadata_uri"]
                    spec_hash = str(proto_hash).split("/")[-1]
                    print(call(iblockchain, spec_hash, method, params))
