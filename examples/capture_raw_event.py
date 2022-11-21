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
    buffer_events_for_bulk_sending=False,
)

event_dict = {"message": "text", "some_injected_field": "injected"}
# client.capture_event(event_dict, level="required")

print("---- ")

event_dict.update({"level": "required"})
client.transport.send_event(event_dict)
