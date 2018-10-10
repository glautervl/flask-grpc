import sys
import os
import json
import hashlib
from pathlib import Path

from organization_utils import get_organization_list, get_organization_list_services
from service_utils import get_service_registration, get_service_endpoint, get_descriptor
from proto_utils import get_proto_file


registry_folder = Path(__file__).absolute().parent.parent
registry_folder = registry_folder.joinpath("registry")


def get_registry_info(iblockchain, out_f=None):
    tmp_stdout = tmp_stderr = None
    if out_f is not None:
        tmp_stdout, tmp_stderr = sys.stdout, sys.stderr
        sys.stdout = out_f
        sys.stderr = out_f

    organizations_json = {}
    org_list = get_organization_list(iblockchain)
    if org_list:
        for idx, organization in enumerate(org_list):
            org = organization.partition(b"\0")[0].decode("utf-8")
            organizations_json[org] = {}
            iblockchain.args.organization_name = organization
            (found, org_services) = get_organization_list_services(iblockchain)
            for idx_s, service in enumerate(org_services):
                srv = service.partition(b"\0")[0].decode("utf-8")
                organizations_json[org][srv] = {}
                iblockchain.args.service_name = service
                (found, _, c_path, c_agent_address, c_tags) = get_service_registration(iblockchain)
                c_path = c_path.partition(b"\0")[0].decode("utf-8")
                c_tags = [tag.partition(b"\0")[0].decode("utf-8") for tag in c_tags]
                organizations_json[org][srv]["path"] = c_path
                organizations_json[org][srv]["agent_address"] = c_agent_address
                organizations_json[org][srv]["tags"] = c_tags
                iblockchain.args.agent_address = c_agent_address
                endpoint = get_service_endpoint(iblockchain)
                organizations_json[org][srv]["endpoint"] = endpoint
                proto_files, metadata_uri = get_proto_file(iblockchain)
                organizations_json[org][srv]["metadata_uri"] = []
                for idx_p, proto_hash in enumerate(proto_files):
                    spec_hash = str(proto_hash).split("/")[-2]
                    organizations_json[org][srv]["metadata_uri"].append(metadata_uri)
                    (service_spec, _, _, _, _) = get_descriptor(spec_hash)
                    organizations_json[org][srv]["service_spec"] = service_spec

        for file in os.listdir(registry_folder):
            if file.endswith(".json"):
                os.remove(str(registry_folder.joinpath(file)))

        filename = hashlib.sha256(json.dumps(organizations_json, sort_keys=True).encode('utf-8')).hexdigest()
        filename = str(registry_folder.joinpath(filename)) + ".json"
        with open(filename, 'w') as outfile:
            json.dump(organizations_json, outfile)

    if None not in [tmp_stdout, tmp_stderr]:
        sys.stdout = tmp_stdout
        sys.stderr = tmp_stderr
    return organizations_json
