import json
import gatey_sdk


def print_transport(event):
    json_string = json.dumps(
        event,
        indent=2,
        sort_keys=True,
    )
    print(json_string)


client = gatey_sdk.Client(transport=print_transport)

client.capture_message("My message", level="INFO")
