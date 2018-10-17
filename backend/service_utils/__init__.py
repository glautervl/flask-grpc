import grpc
import json
import requests
import traceback
from google.protobuf import json_format
from io import StringIO

from snet_cli.commands import ContractCommand, ClientCommand
from snet_cli.utils import get_contract_def

from proto_utils import get_descriptor


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


def get_service_price(iblockchain):
    current_price = None
    try:
        agent_contract_def = get_contract_def("Agent")
        agent_address = iblockchain.args.agent_address
        current_price = ContractCommand(
            config=iblockchain.config,
            args=iblockchain.get_contract_argser(
                contract_address=agent_address,
                contract_function="currentPrice",
                contract_def=agent_contract_def)(),
            out_f=None,
            err_f=None,
            w3=iblockchain.w3,
            ident=iblockchain.ident).call()
    except Exception as e:
        print(e)
    return current_price


def call(job_address, job_signature, endpoint, spec_hash, method, params_string):
    try:
        (services_json, mods, service_name, request_name, response_name) = get_descriptor(spec_hash, method)
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

        channel = grpc.insecure_channel(endpoint.replace("https://", "", 1).replace("http://", "", 1))

        stub = stub_class(channel)
        call_fn = getattr(stub, method)

        params = json.loads(params_string)

        request = request_class()
        json_format.Parse(json.dumps(params), request, True)

        print("Calling service...\n")
        response = call_fn(request, metadata=[("snet-job-address", job_address), ("snet-job-signature", job_signature)])

        return {"response": json.loads(json_format.MessageToJson(response, True, preserving_proto_field_name=True))}
    except Exception as e:
        print(e)
        traceback.print_exc()
        return -1


def call_no_blockchain(endpoint, spec_hash, method, params_string, daemon=False):
    try:
        (services_json, mods, service_name, request_name, response_name) = get_descriptor(spec_hash, method)
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


def call_daemon_static(iblockchain):
    response = StringIO()
    ClientCommand(
        config=iblockchain.config,
        args=iblockchain.args,
        out_f=response,
        err_f=iblockchain.err_f,
        w3=iblockchain.w3,
        ident=iblockchain.ident).call()
    return response
