import gatey_sdk

client = gatey_sdk.Client(transport=lambda _: _)

client.auth.request_oauth_from_stdin()
