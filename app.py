from flask import Flask, render_template, request

import sys
import json
import base64
from random import randint
from threading import Thread
from pathlib import Path

app_folder = Path(__file__).absolute().parent
sys.path.append(str(app_folder.joinpath("backend")))

from backend import mem, update_organization_dict, start_registry_cli, call_api


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


def get_method_info(method, service_spec):
    params = []
    found = False
    for service_s in service_spec:
        for k1, v1 in service_s.items():
            if k1 == "service_spec":
                for k2, v2 in v1.items():
                    for k3, v3 in v2.items():
                        if k3 == "method":
                            if method == v3:
                                found = True
                        if k3 == "request":
                            if found:
                                for k4, v4 in v3.items():
                                    for k5, v5 in v4.items():
                                        for k6, v6 in v5.items():
                                            t = [k4, k6, v6]
                                            params.append(t)
                                return params
    return params


def get_spec_hash(org, srv):
    return mem.organizations_dict[org][srv]["spec_hash"]


def get_simple_json():
    orgs = {}
    for org_name, org_info in mem.organizations_dict.items():
        orgs[org_name] = []
        for service_name, service_info in org_info.items():
            service_list = [service_name]
            for k, v in service_info.items():
                if k == "price":
                    service_list.append("{:.8f}".format(float(v)/10**8))
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


def is_base64(s):
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception as e:
        return False


def response_html(content):
    ret = ""
    if type(content) == dict:
        ret += "<tr>"
        for k, v in content.items():
            ret += "<th class=\"col-md-2\">" + str(k) + "</th>"
            if type(v) == dict:
                ret += response_html(v)
            else:
                if is_base64(str(v).encode()):
                    ret += "<td class=\"col-md-6\"><img src=\"data:image/png;base64, " + str(v) + "\" /></td>"
                else:
                    ret += "<td class=\"col-md-6\">" + str(v) + "</td>"
            ret += "</tr>"
    else:
        ret += "<td class=\"col-md-6\">" + str(content) + "</td>"
    ret += "</tr>"
    return ret


@app.route('/')
def index():
    try:
        update_organization_dict()
        orgs = get_simple_json()
        len_services = 0
        len_orgs = len(orgs)
        for k, v in orgs.items():
            len_services += len(v)
        return render_template("index.html",
                               orgs=orgs,
                               len_orgs=len_orgs,
                               len_services=len_services)
    except Exception as e:
        return str(e)


@app.route('/reload')
def reload():
    update_organization_dict()
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

    if None in [org_name, service_name]:
        return index()

    mem.spec_hash = get_spec_hash(org_name, service_name)

    service_spec = get_service_info(org_name, service_name)
    if service_spec:
        for k, v in service_spec[0].items():
            if k == "agent_address":
                mem.agent_address = str(v).lower()
            if k == "endpoint":
                mem.endpoint = v

    print("[service] agent_address: ", mem.agent_address)
    print("[service] endpoint: ", mem.endpoint)
    print("[service] spec_hash: ", mem.spec_hash)

    return render_template("service.html",
                           org_name=org_name,
                           service_name=service_name,
                           agent_address=mem.agent_address,
                           service_spec=service_spec)


@app.route('/selected_service', methods=['POST', 'GET'])
def selected_service():
    if request.method == 'POST':
        org_name = request.form.get("org")
        service_name = request.form.get("service")
        method = request.form.get("method")
        service_spec = get_service_info(org_name, service_name)
        method_info = get_method_info(method, service_spec)

        print("[selected_service] agent_address: ", mem.agent_address)
        print("[selected_service] method_info: ", method_info)

        return render_template("selected_service.html",
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=mem.agent_address,
                               method=method,
                               method_info=method_info)
    else:
        return index()


@app.route('/createJob', methods=['POST', 'GET'])
def create_job():
    if request.method == 'POST':
        org_name = request.form.get("org")
        service_name = request.form.get("service")
        params = {}
        for k, v in request.form.items():
            if "params#" in k:
                param = k.replace("params#", "")
                params[param] = v
        method = request.form.get("method")
        service_spec = get_service_info(org_name, service_name)
        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info
        create_job_version = randint(1234,1234567)

        print("[create_job] agent_address: ", mem.agent_address)
        print("[create_job] method_info: ", method_info)

        return render_template("createJob.html",
                               create_job_version=create_job_version,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=mem.agent_address,
                               method=method,
                               method_info=method_info)
    else:
        return index()


@app.route('/approveTokens', methods=['POST', 'GET'])
def approve_tokens():
    if request.method == 'POST':
        org_name = request.form.get("org")
        service_name = request.form.get("service")
        params = {}
        for k, v in request.form.items():
            if "params#" in k:
                param = k.replace("params#", "")
                params[param] = v
        method = request.form.get("method")
        service_spec = get_service_info(org_name, service_name)
        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info
        approve_tokens_version = randint(1234, 1234567)

        print("[approveTokens] agent_address: ", mem.agent_address)
        print("[approveTokens] method_info: ", method_info)

        return render_template("approveTokens.html",
                               approve_tokens_version=approve_tokens_version,
                               receipt=mem.receipt,
                               events=mem.events,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=mem.agent_address,
                               method=method,
                               method_info=method_info)
    else:
        return index()


@app.route('/fundJob', methods=['POST', 'GET'])
def fund_job():
    if request.method == 'POST':
        org_name = request.form.get("org")
        service_name = request.form.get("service")
        params = {}
        for k, v in request.form.items():
            if "params#" in k:
                param = k.replace("params#", "")
                params[param] = v
        method = request.form.get("method")
        service_spec = get_service_info(org_name, service_name)
        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info
        fund_job_version = randint(1234, 1234567)

        print("[fund_job] agent_address: ", mem.agent_address)
        print("[fund_job] method_info: ", method_info)

        return render_template("fundJob.html",
                               fund_job_version=fund_job_version,
                               receipt=mem.receipt,
                               events=mem.events,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=mem.agent_address,
                               method=method,
                               method_info=method_info)
    else:
        return index()


@app.route('/callService', methods=['POST', 'GET'])
def call_service():
    if request.method == 'POST':
        org_name = request.form.get("org")
        service_name = request.form.get("service")
        params = {}
        for k, v in request.form.items():
            if "params#" in k:
                param = k.replace("params#", "")
                params[param] = v
        method = request.form.get("method")
        service_spec = get_service_info(org_name, service_name)
        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info
        call_service_version = randint(1234, 1234567)

        print("[call_service] agent_address: ", mem.agent_address)
        print("[call_service] method_info: ", method_info)

        return render_template("callService.html",
                               call_service_version=call_service_version,
                               receipt=mem.receipt,
                               events=mem.events,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=mem.agent_address,
                               method=method,
                               method_info=method_info)
    else:
        return index()


@app.route('/response', methods=['POST', 'GET'])
def response():
    if request.method == 'POST':
        org_name = request.form.get("org")
        service_name = request.form.get("service")
        params = {}
        for k, v in request.form.items():
            if "params#" in k:
                param = k.replace("params#", "")
                params[param] = v
        method = request.form.get("method")
        service_spec = get_service_info(org_name, service_name)
        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info

        res = request.form
        service_response = None
        while not service_response:
            print("agent_address: ", mem.agent_address)
            print("job_address: ", mem.job_address)
            print("job_signature: ", mem.job_signature)
            print("method: ", method)
            print("params: ", json.dumps(params))
            try:
                service_response = call_api(mem.job_address,
                                            mem.job_signature,
                                            mem.endpoint,
                                            mem.spec_hash[0],
                                            method,
                                            json.dumps(params))
                if service_response == -1:
                    raise Exception
            except Exception as e:
                print(e)
                service_response = call_api(mem.job_address,
                                            mem.job_signature,
                                            mem.endpoint,
                                            mem.spec_hash[0],
                                            method,
                                            json.dumps(params))
                break

        if service_response != -1:
            service_response = "<table class=\"table table-hover\">" + response_html(service_response) + "</table>"

        return render_template("response.html",
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=mem.agent_address,
                               method=method,
                               method_info=method_info,
                               response=res,
                               service_response=service_response)
    else:
        return index()


# @app.route('/response', methods=['POST', 'GET'])
# def response_static():
#     if request.method == 'POST':
#         org_name = request.form.get("org")
#         service_name = request.form.get("service")
#         method = request.form.get("method")
#         params = {}
#         for k, v in request.form.items():
#             if "params#" in k:
#                 param = k.replace("params#", "")
#                 params[param] = v
#         agent_address = get_agent_address(org_name, service_name)
#         res = request.form
#         service_response = None
#         while not service_response:
#             print("agent_address: ", agent_address)
#             print("method: ", method)
#             print("params: ", json.dumps(params))
#             try:
#                 service_response = call_service(agent_address, method, json.dumps(params))
#             except Exception as e:
#                 print(e)
#                 service_response = call_service(agent_address, method, json.dumps(params))
#                 break
#         return render_template("response.html",
#                                org_name=org_name,
#                                service_name=service_name,
#                                response=res,
#                                service_response=service_response)


@app.route('/get_receipt', methods=['POST'])
def get_receipt():
    if request.method == 'POST':
        print("============= RECEIPT ================")
        mem.receipt = {}
        for k, v in request.form.items():
            k = k.replace("receipt", "").replace("[", "").replace("]", "")
            print(k, v)
            mem.receipt[k] = v
        return render_template("fundJob.html",
                               events=mem.events,
                               receipt=mem.receipt)


@app.route('/get_events', methods=['POST'])
def get_events():
    if request.method == 'POST':
        print("============= EVENTS ================")
        mem.events = {}
        for k, v in request.form.items():
            print(k, v)
            mem.events[k] = v
        return render_template("fundJob.html",
                               receipt=mem.receipt,
                               events=mem.events)


@app.route('/get_signature', methods=['POST'])
def get_signature():
    if request.method == 'POST':
        print("============= GET SIGNATURE ================")
        for k, v in request.form.items():
            print(k, v)
            if k == "job_address":
                mem.job_address = v
            if k == "job_signature":
                mem.job_signature = v

        return render_template("callService.html",
                               events=mem.events,
                               receipt=mem.receipt)


def main():
    try:
        mem.keep_running = True
        th_registry = Thread(target=start_registry_cli, args=())
        th_registry.daemon = True
        th_registry.start()

        app.run(debug=False, host='0.0.0.0', port=7001, use_reloader=False, passthrough_errors=True)
    except Exception as e:
        print(e)
        mem.keep_running = False


if __name__ == "__main__":
    main()
