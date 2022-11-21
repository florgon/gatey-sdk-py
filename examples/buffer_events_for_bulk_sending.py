import gatey_sdk


def print_transport(event):
    print(event["message"])


client = gatey_sdk.Client(
    transport=print_transport,
    handle_global_exceptions=False,
    buffer_events_for_bulk_sending=True,
    buffer_events_max_capacity=2,
    exceptions_capture_vars=False,
)

# Will send requests on second.
client.capture_message("info", "hi!")
client.capture_message("info", "hi!")


# Will send requests with call.
client.capture_message("info", "hi!")
client.bulk_send_buffered_events()

# Will send request after script end.
client.capture_message("info", "hi!")
