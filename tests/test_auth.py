import gatey_sdk

client = gatey_sdk.Client(access_token="my_token")
client.change_api_provider("https://api.florgon.space/gatey")  # DEFAULT.


print(
    client._parse_access_token_from_redirect_uri(
        "https://florgon.space/oauth/blank?access_token=my_token"
    )
)
