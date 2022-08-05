"""
    Resolve exception to params with all data sent to the server.
"""

import json
import gatey_sdk

client = gatey_sdk.Client()

try:
    raise BaseException("Message from exception!")
except BaseException as e:
    params = client.resolve_exception_to_params(e, include_vars=False)
    json_string = json.dumps(
        params,
        indent=2,
        sort_keys=True,
    )
    print(json_string)
