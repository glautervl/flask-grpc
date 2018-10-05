from snet_cli.commands import BlockchainCommand, ContractCommand
from snet_cli.utils import get_contract_def, compile_proto

from configparser import ConfigParser, ExtendedInterpolation
import web3
import requests
import json
import os
import sys
import io
import tarfile
import grpc
from google.protobuf import json_format
import ipfsapi
from pathlib import Path
from rfc3986 import urlparse
from urllib.parse import urljoin

import traceback


class CustomArgs:
    def __init__(self):
        self.organization_name = ""
        self.service_name = ""
        self.agent_address = ""


def get_ipfs_client(config):
    ipfs_endpoint = urlparse(config["ipfs"]["default_ipfs_endpoint"])
    ipfs_scheme = ipfs_endpoint.scheme if ipfs_endpoint.scheme else "http"
    ipfs_port = ipfs_endpoint.port if ipfs_endpoint.port else 5001
    return ipfsapi.connect(urljoin(ipfs_scheme, ipfs_endpoint.hostname), ipfs_port)


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


def get_conf():
    conf = ConfigParser(interpolation=ExtendedInterpolation(), delimiters=("=",))

    try:
        with open("./config") as f:
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
    return conf


def get_metadata_uri(iblockchain):
    response = None
    try:
        agent_contract_def = get_contract_def("Agent")
        agent_address = iblockchain.args.agent_address
        response = ContractCommand(
            config=iblockchain.config,
            args=iblockchain.get_contract_argser(
                contract_address=agent_address,
                contract_function="metadataURI",
                contract_def=agent_contract_def)(),
            out_f=None,
            err_f=None,
            w3=iblockchain.w3,
            ident=iblockchain.ident).call()
        return response
    except Exception as e:
        print(e)
    return response


def get_proto_file(iblockchain):
    try:
        metadata_uri = get_metadata_uri(iblockchain)
        ipfs_client = get_ipfs_client(iblockchain.config)
        spec_hash = json.loads(ipfs_client.cat(metadata_uri.split("/")[-1]))["modelURI"].split("/")[-1]

        spec_dir = Path("~").expanduser().joinpath(".snet").joinpath("service_spec").joinpath(spec_hash)
        if not os.path.exists(spec_dir):
            os.makedirs(spec_dir)
        spec_tar = ipfs_client.cat(spec_hash)
        with tarfile.open(fileobj=io.BytesIO(spec_tar)) as f:
            f.extractall(spec_dir)
        response = []
        for idx, filename in enumerate(os.listdir(spec_dir)):
            response.append(spec_dir.joinpath(filename))
        return response
    except Exception as e:
        print(e)
        return None


def get_organization_list(iblockchain):
    response = None
    try:
        registry_contract_def = get_contract_def("Registry")
        registry_address = iblockchain._getstring("registry_at")
        response = ContractCommand(
            config=iblockchain.config,
            args=iblockchain.get_contract_argser(
                contract_address=registry_address,
                contract_function="listOrganizations",
                contract_def=registry_contract_def)(),
            out_f=None,
            err_f=None,
            w3=iblockchain.w3,
            ident=iblockchain.ident).call()
    except Exception as e:
        print(e)
    return response


def get_organization_list_services(iblockchain):
    response = None
    try:
        registry_contract_def = get_contract_def("Registry")
        registry_address = iblockchain._getstring("registry_at")
        org_name = iblockchain.args.organization_name
        response = ContractCommand(
            config=iblockchain.config,
            args=iblockchain.get_contract_argser(
                contract_address=registry_address,
                contract_function="listServicesForOrganization",
                contract_def=registry_contract_def)(org_name),
            out_f=None,
            err_f=None,
            w3=iblockchain.w3,
            ident=iblockchain.ident).call()
    except Exception as e:
        print(e)
    return response


def get_service_registration(iblockchain):
    response = None
    try:
        registry_contract_def = get_contract_def("Registry")
        registry_address = iblockchain._getstring("registry_at")
        org_name = iblockchain.args.organization_name
        serv_name = iblockchain.args.service_name
        return ContractCommand(
            config=iblockchain.config,
            args=iblockchain.get_contract_argser(
                contract_address=registry_address,
                contract_function="getServiceRegistrationByName",
                contract_def=registry_contract_def)(org_name,
                                                    serv_name),
            out_f=None,
            err_f=None,
            w3=iblockchain.w3,
            ident=iblockchain.ident).call()
    except Exception as e:
        print(e)
    return response


def get_service_endpoint(iblockchain):
    response = None
    try:
        agent_contract_def = get_contract_def("Agent")
        agent_address = iblockchain.args.agent_address
        response = ContractCommand(
            config=iblockchain.config,
            args=iblockchain.get_contract_argser(
                contract_address=agent_address,
                contract_function="endpoint",
                contract_def=agent_contract_def)(),
            out_f=None,
            err_f=None,
            w3=iblockchain.w3,
            ident=iblockchain.ident).call()
    except Exception as e:
        print(e)
    return response


def call_service(iblockchain, spec_hash, method, params_string):
    try:
        spec_dir = Path("~").expanduser().joinpath(".snet").joinpath("service_spec").joinpath(spec_hash)
        codegen_dir = Path("~").expanduser().joinpath(".snet").joinpath("py-codegen").joinpath(spec_hash)
        compile_proto(spec_dir, codegen_dir)

        sys.path.append(str(codegen_dir))
        mods = []
        for p in codegen_dir.glob("*_pb2*"):
            m = __import__(p.name.replace(".py", ""))
            print("sys.getrefcount({}): {}".format(m, sys.getrefcount(m)))
            mods.append(m)

        service_name = None
        request_name = None
        response_name = None
        for mod in mods:
            desc = getattr(mod, "DESCRIPTOR", None)
            if desc is not None:
                for s_name, s_desc in desc.services_by_name.items():
                    for m_desc in s_desc.methods:
                        print("Method: ", m_desc.name)
                        # if m_desc.name == method:
                        service_name = s_name
                        request_name = m_desc.input_type.name
                        print("\tRequest: ", request_name)
                        for idx, field in enumerate(m_desc.input_type.fields):
                            print("\t\tParam: [{}] {}".format(field.type, field.name))
                        response_name = m_desc.output_type.name
                        print("\tResponse: ", response_name)
                        for idx, field in enumerate(m_desc.output_type.fields):
                            print("\t\tParam: [{}] {}".format(field.type, field.name))

            del sys.modules[mod.__name__]
            input("CTRL+C")

        if None in [service_name, request_name, response_name]:
            print("Failed to load service spec")
            return None

        return

        stub_class = None
        request_class = None
        response_class = None
        for mod in mods:
            if stub_class is None:
                stub_class = getattr(mod, service_name + "Stub", None)
            if request_class is None:
                request_class = getattr(mod, request_name, None)
            if response_class is None:
                response_class = getattr(mod, response_name, None)

        if None in [stub_class, request_class, response_class]:
            print("Failed to load service spec")
            return None

        endpoint = get_service_endpoint(iblockchain)
        print("endpoint: ", endpoint)
        endpoint = "localhost:7004"
        endpoint = "http://54.203.198.53:7005"
        channel = grpc.insecure_channel(endpoint.replace("https://", "", 1).replace("http://", "", 1))

        stub = stub_class(channel)
        call_fn = getattr(stub, method)

        params = json.loads(params_string)

        request = request_class()
        json_format.Parse(json.dumps(params), request, True)

        # encoding = requests.get(endpoint + "/encoding").text.strip()
        encoding = "proto"
        if encoding == "json":
            def json_serializer(*args, **kwargs):
                return bytes(json_format.MessageToJson(args[0], True, preserving_proto_field_name=True), "utf-8")

            def json_deserializer(*args, **kwargs):
                resp = response_class()
                json_format.Parse(args[0], resp, True)
                return resp

            call_fn._request_serializer = json_serializer
            call_fn._response_deserializer = json_deserializer

        print("Calling service...\n")
        response = call_fn(request)
        return {"response": json.loads(json_format.MessageToJson(response, True, preserving_proto_field_name=True))}
    except Exception as e:
        print(e)
        traceback.print_exc()


def main():
    args = CustomArgs()
    conf = get_conf()
    iblockchain = BlockchainCommand(conf, args)

    # List Organizations
    org_list = get_organization_list(iblockchain)
    if org_list:
        print("List of Organizations:")
        for idx, organization in enumerate(org_list):
            print("{}: {}".format(idx+1, organization.decode('utf-8')))
            iblockchain.args.organization_name = organization
            (found, org_services) = get_organization_list_services(iblockchain)
            for idx_s, service in enumerate(org_services):
                print("\t{}: {}".format(idx_s+1, service.decode('utf-8')))
                iblockchain.args.service_name = service
                (found, _, current_path, current_agent_address, current_tags) = get_service_registration(iblockchain)
                print("\t\tAddress: {}".format(current_agent_address))
                # print("\tTAGs: {}".format([t.decode('utf-8') for t in current_tags]))
                iblockchain.args.agent_address = current_agent_address
                proto_files = get_proto_file(iblockchain)
                print("\t\tProtoFolder: {}".format(proto_files))
                # if current_agent_address == "0x1E89D9ed5bCC22F934AF631CdA771019081E57B2":
                for idx_p, proto_hash in enumerate(proto_files):
                    spec_hash = str(proto_hash).split("/")[-2]
                    # method = input("Method: ")
                    # params = input("Params: ")
                    print(call_service(iblockchain, spec_hash, "method", "params"))
            print()


if __name__ == "__main__":
    main()
