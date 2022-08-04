"""
    Auth process.
"""
import gatey_sdk

client = gatey_sdk.Client(access_token="")

redirect_uri = "https://florgon.space/oauth/blank?access_token=my_token"
access_token = client._parse_access_token_from_redirect_uri(redirect_uri)

client.change_access_token(access_token=access_token)
