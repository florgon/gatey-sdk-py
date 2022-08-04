"""
    Custom API provider (Self-Hosted)
"""
import gatey_sdk

api_provider = "https://api.florgon.space/gatey"
client = gatey_sdk.Client(api_provider=api_provider)
client.change_api_provider(api_provider)
