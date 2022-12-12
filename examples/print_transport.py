import gatey_sdk

client = gatey_sdk.Client(
    transport=gatey_sdk.PrintTransport,
    exceptions_capture_vars=False,
    handle_global_exceptions=True,
    global_handler_skip_internal_exceptions=True,
)

raise ValueError("Message from exception!")
