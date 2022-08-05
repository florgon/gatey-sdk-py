"""
    Resolve exception to params with all data sent to the server.
"""

import json
import gatey_sdk


def ft(event):
    json_string = json.dumps(
        event,
        indent=2,
        sort_keys=True,
    )
    print(json_string)


client = gatey_sdk.Client(transport=ft, capture_vars=False)


@client.catch(
    reraise=False,
    exception=BaseException,
    ignored_exceptions=[],
    skip_global_handler_on_ignore=False,
)
def test_wrapped():
    print("Message before exception fire")
    raise TypeError
    print("Message after exception fire")


raise BaseException("Message from exception!")


test_wrapped()
try:
    raise ValueError
except Exception as e:
    client.capture_exception(e)
