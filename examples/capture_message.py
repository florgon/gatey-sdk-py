import gatey_sdk

client = gatey_sdk.Client(transport=gatey_sdk.PrintTransport)

client.capture_message("My message", level="INFO")
