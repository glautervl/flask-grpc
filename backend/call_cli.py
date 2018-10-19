import os
import sys
import json
from pathlib import Path

from service_utils import call


def main():
    file_path = None
    try:
        if len(sys.argv) == 7:
            job_address = sys.argv[1]
            job_signature = sys.argv[2]
            endpoint = sys.argv[3]
            spec_hash = sys.argv[4]
            method = sys.argv[5]
            params = sys.argv[6]

            # Long params (base64)
            if params == job_address:
                file_path = Path().joinpath("tmp").joinpath(job_address + ".txt")
                with open(file_path) as f:
                    params = json.load(f)
            else:
                params = json.loads(params)

            tmp_params = {}
            for k,v in params.items():
                if v != "":
                    tmp_params[k] = v
            params = json.dumps(tmp_params)

            print(call(job_address, job_signature, endpoint, spec_hash, method, params))

            if file_path and os.path.exists(file_path):
                os.remove(str(file_path))
        else:
            print("Invalid number of Params!")
    except Exception as e:
        print(e)
        if file_path and os.path.exists(file_path):
            os.remove(str(file_path))
        return


if __name__ == "__main__":
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
    main()
