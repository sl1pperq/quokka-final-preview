import sys
from io import StringIO


def run_code(code, input_data):
    sys.stdin = StringIO(input_data)
    output = StringIO()
    sys.stdout = output
    exec(code)
    output_data = output.getvalue()
    return output_data
