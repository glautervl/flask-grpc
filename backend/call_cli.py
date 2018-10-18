import os
import sys
from service_utils import call


def main():
    try:
        if len(sys.argv) == 7:
            job_address = sys.argv[1]
            job_signature = sys.argv[2]
            endpoint = sys.argv[3]
            spec_hash = sys.argv[4]
            method = sys.argv[5]
            params = sys.argv[6]
            print(call(job_address, job_signature, endpoint, spec_hash, method, params))
        else:
            print("Invalid number of Params!")
    except Exception as e:
        print(e)
        return


if __name__ == "__main__":
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
    main()
