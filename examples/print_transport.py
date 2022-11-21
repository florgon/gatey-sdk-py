import json
import gatey_sdk


def print_transport(event):
    json_string = json.dumps(
        event,
        indent=2,
        sort_keys=True,
    )
    print(json_string)


client = gatey_sdk.Client(
    transport=print_transport,
    exceptions_capture_vars=False,
    handle_global_exceptions=True,
    global_handler_skip_internal_exceptions=True,
)


raise ValueError("Message from exception!")
