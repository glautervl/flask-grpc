from snet_cli.commands import ContractCommand
from snet_cli.utils import get_contract_def


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
