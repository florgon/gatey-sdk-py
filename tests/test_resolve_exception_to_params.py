import gatey_sdk
import json

client = gatey_sdk.Client()


try:
    raise BaseException("test")
except BaseException as e:
    print(
        json.dumps(
            client.resolve_exception_to_params(e, include_vars=False),
            indent=2,
            sort_keys=True,
        )
    )
