import gatey_sdk

client = gatey_sdk.Client(access_token="my_token")
client.change_api_provider("https://api.florgon.space/gatey")  # DEFAULT.

print(client.methods.utils_get_server_time())

t_diff = client.get_server_time_difference()
if t_diff > 10:
    print("Server and client time is too much runs out")
else:
    print("Server and client time is not runs out")
    print(f"Time diff: {t_diff}")

print(
    client._parse_access_token_from_redirect_uri(
        "https://florgon.space/oauth/blank?access_token=my_token"
    )
)
