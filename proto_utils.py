import sys
import os
import json
import io
import importlib
import tarfile
import ipfsapi
from rfc3986 import urlparse
from urllib.parse import urljoin
from pathlib import Path
import traceback

from snet_cli.commands import ContractCommand
from snet_cli.utils import get_contract_def, compile_proto


def get_ipfs_client(config):
    ipfs_endpoint = urlparse(config["ipfs"]["default_ipfs_endpoint"])
    ipfs_scheme = ipfs_endpoint.scheme if ipfs_endpoint.scheme else "http"
    ipfs_port = ipfs_endpoint.port if ipfs_endpoint.port else 5001
    return ipfsapi.connect(urljoin(ipfs_scheme, ipfs_endpoint.hostname), ipfs_port)


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
        return response, metadata_uri
    except Exception as e:
        print(e)
        return None


def import_grpc_modules(spec_hash):
    spec_dir = Path("~").expanduser().joinpath(".snet").joinpath("service_spec").joinpath(spec_hash)
    codegen_dir = Path("~").expanduser().joinpath(".snet").joinpath("py-codegen").joinpath(spec_hash)

    sys.path.append(str(codegen_dir))
    compile_proto(spec_dir, codegen_dir)

    mods = []
    for p in codegen_dir.glob("*_pb2*"):
        m = importlib.import_module(p.name.replace(".py", ""))
        mods.append(m)
    # sys.path.remove(str(codegen_dir))
    return mods


def get_descriptor(spec_hash, method=None):
    try:
        mods = import_grpc_modules(spec_hash)
        services_json = {}
        method_found = False
        service_name = None
        request_name = None
        response_name = None
        for mod in mods:
            desc = getattr(mod, "DESCRIPTOR", None)
            if desc is not None:
                for s_name, s_desc in desc.services_by_name.items():
                    services_json[s_name] = {}
                    for m_desc in s_desc.methods:
                        services_json[s_name]["method"] = m_desc.name
                        if not method_found:
                            service_name = s_name
                            request_name = m_desc.input_type.name
                        services_json[s_name]["request"] = {}
                        services_json[s_name]["request"][m_desc.input_type.name] = {}
                        services_json[s_name]["request"][m_desc.input_type.name]["param"] = {}
                        for idx, field in enumerate(m_desc.input_type.fields):
                            services_json[s_name]["request"][m_desc.input_type.name]["param"][field.name] = {}
                            services_json[s_name]["request"][m_desc.input_type.name]["param"][field.name]["type"] = field.type
                            services_json[s_name]["request"][m_desc.input_type.name]["param"][field.name]["name"] = field.name
                        if not method_found:
                            response_name = m_desc.output_type.name
                        services_json[s_name]["response"] = {}
                        services_json[s_name]["response"][m_desc.output_type.name] = {}
                        services_json[s_name]["response"][m_desc.output_type.name]["param"] = {}
                        for idx, field in enumerate(m_desc.output_type.fields):
                            services_json[s_name]["response"][m_desc.output_type.name]["param"][field.name] = {}
                            services_json[s_name]["response"][m_desc.output_type.name]["param"][field.name]["type"] = field.type
                            services_json[s_name]["response"][m_desc.output_type.name]["param"][field.name]["name"] = field.name
                        if m_desc.name == method:
                            service_name = s_name
                            request_name = m_desc.input_type.name
                            response_name = m_desc.output_type.name
                            method_found = True
        if None in [service_name, request_name, response_name]:
            print("Failed to load service spec")
            return {}, [], None, None, None
        return services_json, mods, service_name, request_name, response_name
    except Exception as e:
        print(e)
        traceback.print_exc()
        return {}, [], None, None, None
