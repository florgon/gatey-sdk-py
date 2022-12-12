import gatey_sdk

client = gatey_sdk.Client(transport=gatey_sdk.PrintTransport)

try:
    raise ValueError("Message text!")
except Exception as e:
    client.capture_exception(e, level="error")
