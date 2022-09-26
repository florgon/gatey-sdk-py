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


print(gatey_sdk.__version__)
# client = gatey_sdk.Client(transport=ft, capture_vars=False)
client = gatey_sdk.Client(
    transport=gatey_sdk.HttpTransport,
    capture_vars=False,
    handle_global_exceptions=True,
    global_handler_skip_internal_exceptions=True,
    project_id=1,
    client_secret="",
    server_secret=None,
    access_token=None,
    check_api_auth_on_init=False,
)


@client.catch(
    reraise=True,
    exception=BaseException,
    ignored_exceptions=[],
    skip_global_handler_on_ignore=False,
)
def test_wrapped():
    print("Message before exception fire")
    raise TypeError("message text")
    print("Message after exception fire")


# raise BaseException("Message from exception!")


test_wrapped()
# try:
#    raise ValueError
# except Exception as e:
#    client.capture_exception(e)
