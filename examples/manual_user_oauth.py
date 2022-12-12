import gatey_sdk

client = gatey_sdk.Client(transport=gatey_sdk.VoidTransport)

client.auth.request_oauth_from_stdin()
