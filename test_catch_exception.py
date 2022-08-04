import gatey_sdk

client = gatey_sdk.Client()


try:
    raise BaseException("test")
except BaseException as e:
    print(client.resolve_exception_to_params(e))
