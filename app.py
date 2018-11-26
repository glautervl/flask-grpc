from flask import Flask, render_template, session, request

import os
import sys
import json
import base64
from random import randint
from threading import Thread
from pathlib import Path

app_folder = Path(__file__).absolute().parent
sys.path.append(str(app_folder.joinpath("backend")))

from backend import mem, update_organization_dict, start_registry_cli, call_api, get_wallet_by_mnemonic


# For protobuf
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

app = Flask(__name__)
app.config.from_object("config")


def get_service_info(org_dict, target_org, target_service):
    service_spec = []
    for org_name, org_info in org_dict.items():
        if org_name == target_org:
            for service_name, service_info in org_info.items():
                if service_name == target_service:
                    service_spec.append(service_info)

    agent_address = ""
    endpoint = ""
    if service_spec:
        for k, v in service_spec[0].items():
            if k == "agent_address":
                agent_address = str(v).lower()
            if k == "endpoint":
                endpoint = v

    return service_spec, agent_address, endpoint


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


def get_spec_hash(org_dict, org, srv):
    d = org_dict.get(org, None)
    d = d.get(srv, None)
    return d.get("spec_hash", None)


def get_simple_json(org_dict):
    orgs = {}
    for org_name, org_info in org_dict.items():
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
                if is_base64(str(v).encode()) and len(str(v)) > 500:
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
        org_dict = update_organization_dict()
        orgs = get_simple_json(org_dict)
        len_services = 0
        len_orgs = len(orgs)
        for k, v in orgs.items():
            len_services += len(v)

        user_account = session.get("user_account", "")
        print("[index] user_account: ", user_account)

        return render_template("index.html",
                               user_account=user_account,
                               orgs=orgs,
                               len_orgs=len_orgs,
                               len_services=len_services)
    except Exception as e:
        return str(e)


@app.route('/reload')
def reload():
    org_dict = update_organization_dict()
    len_orgs = len(org_dict)
    len_services = 0
    for _, services in org_dict.items():
        for _, _ in services.items():
            len_services += 1

    user_account = session.get("user_account", "")
    print("[reload] user_account: ", user_account)

    return render_template("index.html",
                           user_account=user_account,
                           org_json=org_dict,
                           len_orgs=len_orgs,
                           len_services=len_services)


@app.route('/wallet', methods=['POST', 'GET'])
def wallet():
    user_wallet = {
        "address": "Fail",
        "private_key": "Fail"
    }
    if request.method == 'POST':
        user_wallet = get_wallet_by_mnemonic(request.form.get("mnemonic"), request.form.get("index"))
        print("[wallet] user_wallet: ", user_wallet)

    return render_template("wallet.html",
                           service_name="Wallet Generator",
                           user_wallet=user_wallet)


@app.route('/service')
def service():
    org_name = request.args.get("org")
    service_name = request.args.get("service")

    if None in [org_name, service_name]:
        return index()

    org_dict = update_organization_dict()
    spec_hash = get_spec_hash(org_dict, org_name, service_name)
    service_spec, agent_address, endpoint = get_service_info(org_dict, org_name, service_name)

    user_account = session.get("user_account", "")
    print("[service] user_account: ", user_account)
    print("[service] agent_address: ", agent_address)
    print("[service] endpoint: ", endpoint)
    print("[service] spec_hash: ", spec_hash)

    return render_template("service.html",
                           user_account=user_account,
                           org_name=org_name,
                           service_name=service_name,
                           agent_address=agent_address,
                           service_spec=service_spec)


@app.route('/selected_service', methods=['POST', 'GET'])
def selected_service():
    if request.method == 'POST':
        org_name = request.form.get("org")
        service_name = request.form.get("service")
        method = request.form.get("method")

        org_dict = update_organization_dict()
        service_spec, agent_address, endpoint = get_service_info(org_dict, org_name, service_name)
        method_info = get_method_info(method, service_spec)

        user_account = session.get("user_account", "")
        print("[selected_service] user_account: ", user_account)
        print("[selected_service] agent_address: ", agent_address)
        print("[selected_service] method_info: ", method_info)

        return render_template("selected_service.html",
                               user_account=user_account,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=agent_address,
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

        org_dict = update_organization_dict()
        service_spec, agent_address, endpoint = get_service_info(org_dict, org_name, service_name)

        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info
        create_job_version = randint(1234,1234567)

        user_account = session.get("user_account", "")
        print("[create_job] user_account: ", user_account)
        print("[create_job] agent_address: ", agent_address)
        print("[create_job] method_info: ", method_info)

        return render_template("createJob.html",
                               user_account=user_account,
                               create_job_version=create_job_version,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=agent_address,
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

        org_dict = update_organization_dict()
        service_spec, agent_address, endpoint = get_service_info(org_dict, org_name, service_name)

        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info
        approve_tokens_version = randint(1234, 1234567)

        receipt = session.get("receipt", {})
        events = session.get("events", {})

        user_account = session.get("user_account", "")
        print("[approveTokens] user_account: ", user_account)
        print("[approveTokens] agent_address: ", agent_address)
        print("[approveTokens] method_info: ", method_info)

        return render_template("approveTokens.html",
                               user_account=user_account,
                               approve_tokens_version=approve_tokens_version,
                               receipt=receipt,
                               events=events,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=agent_address,
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

        org_dict = update_organization_dict()
        service_spec, agent_address, endpoint = get_service_info(org_dict, org_name, service_name)

        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info
        fund_job_version = randint(1234, 1234567)

        receipt = session.get("receipt", {})
        events = session.get("events", {})

        user_account = session.get("user_account", "")
        print("[fund_job] user_account: ", user_account)
        print("[fund_job] agent_address: ", agent_address)
        print("[fund_job] method_info: ", method_info)

        return render_template("fundJob.html",
                               user_account=user_account,
                               fund_job_version=fund_job_version,
                               receipt=receipt,
                               events=events,
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

        org_dict = update_organization_dict()
        service_spec, agent_address, endpoint = get_service_info(org_dict, org_name, service_name)

        method_info = get_method_info(method, service_spec)
        tmp_method_info = []
        for method_i in method_info:
            l = method_i
            l.append(params[method_i[1]])
            tmp_method_info.append(l)
        method_info = tmp_method_info
        call_service_version = randint(1234, 1234567)

        receipt = session.get("receipt", {})
        events = session.get("events", {})

        user_account = session.get("user_account", "")
        print("[call_service] user_account: ", user_account)
        print("[call_service] agent_address: ", agent_address)
        print("[call_service] method_info: ", method_info)

        return render_template("callService.html",
                               user_account=user_account,
                               call_service_version=call_service_version,
                               receipt=receipt,
                               events=events,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=agent_address,
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

        org_dict = update_organization_dict()
        spec_hash = get_spec_hash(org_dict, org_name, service_name)
        service_spec, agent_address, endpoint = get_service_info(org_dict, org_name, service_name)

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
            user_account = session.get("user_account", "")
            job_address = session.get("job_address", "")
            job_signature = session.get("job_signature", "")

            print("[response] user_account: ", user_account)
            print("[response] agent_address: ", agent_address)
            print("[response] job_address: ", job_address)
            print("[response] job_signature: ", job_signature)
            print("[response] method: ", method)

            # If Base64 images, creates a file with it.
            # Sends the params equal to job_address.
            if len(json.dumps(params)) > 500:
                tmp_folder = app_folder.joinpath("backend").joinpath("tmp")
                if not os.path.exists(tmp_folder):
                    os.makedirs(tmp_folder)
                file_path = tmp_folder.joinpath(job_address + ".txt")
                with open(file_path, "w") as f:
                    f.write(json.dumps(params))
                params = job_address
            else:
                params = json.dumps(params)

            print("[response] params: ", params)

            try:
                service_response = call_api(job_address,
                                            job_signature,
                                            endpoint,
                                            spec_hash[0],
                                            method,
                                            params)
                if not service_response or service_response == -1:
                    raise Exception
            except Exception as e:
                print(e)
                service_response = call_api(job_address,
                                            job_signature,
                                            endpoint,
                                            spec_hash[0],
                                            method,
                                            params)
                break

        if service_response != -1:
            service_response = "<table class=\"table table-hover\">" + response_html(service_response) + "</table>"

        return render_template("response.html",
                               user_account=user_account,
                               org_name=org_name,
                               service_name=service_name,
                               agent_address=agent_address,
                               method=method,
                               method_info=method_info,
                               response=res,
                               service_response=service_response)
    else:
        return index()


@app.route('/get_user_account', methods=['POST'])
def get_user_account():
    session["user_account"] = ""
    if request.method == 'POST':
        print("============= GET ACCOUNT ================")
        for k, v in request.form.items():
            print(k, v)
            if k == "user_account":
                session["user_account"] = v
    return ""


@app.route('/get_receipt', methods=['POST'])
def get_receipt():
    if request.method == 'POST':
        print("============= RECEIPT ================")
        receipt = {}
        for k, v in request.form.items():
            k = k.replace("receipt", "").replace("[", "").replace("]", "")
            print(k, v)
            receipt[k] = v
        session["receipt"] = receipt
    return ""


@app.route('/get_events', methods=['POST'])
def get_events():
    if request.method == 'POST':
        print("============= EVENTS ================")
        events = {}
        for k, v in request.form.items():
            print(k, v)
            events[k] = v
        session["events"] = events
    return ""


@app.route('/get_signature', methods=['POST'])
def get_signature():
    if request.method == 'POST':
        print("============= GET SIGNATURE ================")
        for k, v in request.form.items():
            print(k, v)
            if k == "job_address":
                session["job_address"] = v
            if k == "job_signature":
                session["job_signature"] = v
    return ""


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
