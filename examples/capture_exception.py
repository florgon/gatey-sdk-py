import gatey_sdk

client = gatey_sdk.Client(transport=gatey_sdk.PrintTransport)

try:
    raise ValueError("Message text!")
except Exception as e:
    client.capture_exception(e, level="error")

try:
    raise ValueError("Message text for local getter!")
except Exception:
    # Same as above but gets from current.
    client.capture_exception()


@client.catch(reraise=False)
def my_func():
    raise ValueError("Message text from wrapped function")


my_func()
