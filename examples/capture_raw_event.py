import gatey_sdk

client = gatey_sdk.Client(
    transport=gatey_sdk.PrintTransport,
    buffer_events_for_bulk_sending=False,
)

event_dict = {"message": "text", "some_injected_field": "injected"}

client.capture_event(event_dict, level="required")

print("---- ")

event_dict.update({"level": "required"})
client.transport.send_event(event_dict)
