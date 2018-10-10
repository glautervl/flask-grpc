from flask import Flask, render_template, request

import sys
import json
from pathlib import Path
app_folder = Path(__file__).absolute().parent
sys.path.append(str(app_folder.joinpath("backend")))

from backend import update_organization_dict, start_registry_cli, mem, call_service


app = Flask(__name__)
update_organization_dict()


def get_service_info(target_org, target_service):
    service_dict_list = []
    for org_name, org_info in mem.organizations_dict.items():
        if org_name == target_org:
            for service_name, service_info in org_info.items():
                if service_name == target_service:
                    service_dict_list.append(service_info)
    return service_dict_list


def get_simple_json():
    orgs = {}
    for org_name, org_info in mem.organizations_dict.items():
        orgs[org_name] = []
        for service_name, service_info in org_info.items():
            service_list = [service_name]
            for k, v in service_info.items():
                if k == "agent_address":
                    service_list.append(v)
                if k == "endpoint":
                    service_list.append(v)
            orgs[org_name].append(service_list)
    return orgs


def get_agent_address(target_org, target_service):
    orgs = get_simple_json()
    address = ""
    for org_name, services_info in orgs.items():
        if org_name == target_org:
            for item in services_info:
                if item[0] == target_service:
                    address = item[1]
                    break
    return address


@app.route('/')
def index():
    try:
        update_organization_dict()
        orgs = get_simple_json()
        len_services = 0
        len_orgs = len(orgs)
        for k, v in orgs.items():
            len_services += len(v)
        # print(json.dumps(mem.organizations_dict, sort_keys=True, indent=4))
        return render_template("index.html",
                               orgs=orgs,
                               len_orgs=len_orgs,
                               len_services=len_services)
    except Exception as e:
        return str(e)


@app.route('/reload')
def reload():
    start_registry_cli()
    len_orgs = len(mem.organizations_dict)
    len_services = 0
    for _, services in mem.organizations_dict.items():
        for _, _ in services.items():
            len_services += 1
    return render_template("index.html",
                           org_json=mem.organizations_dict,
                           len_orgs=len_orgs,
                           len_services=len_services)


@app.route('/service')
def service():
    org_name = request.args.get("org")
    service_name = request.args.get("service")
    service_spec = get_service_info(org_name, service_name)
    return render_template("service.html",
                           org_name=org_name,
                           service_name=service_name,
                           service_spec=service_spec)


@app.route('/response', methods=['POST', 'GET'])
def response():
    if request.method == 'POST':
        org_name = request.form.get("org")
        service_name = request.form.get("service")
        method = request.form.get("method")
        params = {}
        for k, v in request.form.items():
            if "params#" in k:
                param = k.replace("params#", "")
                params[param] = v
        agent_address = get_agent_address(org_name, service_name)
        res = request.form
        print("agent_address: ", agent_address)
        print("method: ", method)
        print("params: ", json.dumps(params))
        service_response = call_service(agent_address, method, json.dumps(params))
        return render_template("response.html",
                               org_name=org_name,
                               service_name=service_name,
                               response=res,
                               service_response=service_response)


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=7001, use_reloader=False, passthrough_errors=True)