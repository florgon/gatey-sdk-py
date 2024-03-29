import gatey_sdk


client = gatey_sdk.Client(
    transport=gatey_sdk.PrintTransport(prepare_event=lambda e: e["message"]),
    handle_global_exceptions=False,
    buffer_events_for_bulk_sending=True,
    buffer_events_max_capacity=2,
    exceptions_capture_vars=False,
)

# Will send requests on second call.
client.capture_message("info", "hi!")
client.capture_message("info", "hi!")

# Will not capture any.
client.events_buffer.max_capacity = 0
client.capture_message("info", "hi!")
client.capture_message("info", "hi!")
client.events_buffer.clear_events()  # Or `legacy` way as `client.force_drop_buffered_events()`
client.events_buffer.send_all()  # Or `legacy` way as `client.bulk_send_buffered_events()`
client.events_buffer.max_capacity = 2

# Will send requests with second (send) call.
client.capture_message("info", "hi!")
client.events_buffer.send_all()  # Or `legacy` way as `client.bulk_send_buffered_events()`

# Will send request after script end.
client.capture_message("info", "hi!")
