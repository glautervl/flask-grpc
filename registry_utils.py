import json

from organization_util import get_organization_list, get_organization_list_services
from service_utils import get_service_registration, get_service_endpoint, get_descriptor, call, call_daemon
from proto_utils import get_proto_file


def get_registry_info(iblockchain):
    org_list = get_organization_list(iblockchain)
    if org_list:
        organizations_json = {}
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
        return organizations_json
    else:
        print("No Organization found!")
        return None
