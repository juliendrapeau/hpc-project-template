import json
import sys


def loads_json(file):
    parameters = json.loads(file)
    return parameters


if __name__ == "__main__":

    # Try to read parameters from the command line
    if len(sys.argv) == 2:
        json_file = sys.argv[1]
        params = loads_json(json_file)

        param1 = params["param1"]
        # Add more parameters if needed

    # If no parameters are provided, choose them manually
    elif len(sys.argv) == 1:

        param1 = 0

    else:
        print("Usage: python script.py or python script.py param_json_dict")
        sys.exit(1)
