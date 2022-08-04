"""
    Florgon Gatey SDK.

    SDK Library for Florgon Gatey API.
    Provides interface for working with Florgon Gatey.

    Florgon Gatey is a error logging service.
    Library provides interface for working with exceptions, catching them,
    Working with message / events and all another analytics stuff,
    Also there is base API interface, allowing to work with native API, not base gateway end-user API.

    Author: Florgon Solutions.
    Gatey website: https://gatey.florgon.space/
    Gatey API endpoint: https://api.florgon.space/gatey/
    Gatey developer documentation: https://gatey-sdk-py.readthedocs.io/

    If you have any questions please reach out us at:
    - support@florgon.space

    Main SDK maintainer:
    - Kirill Zhosul (@kirillzhosul)
    - kirillzhosul@florgon.space
    - https://github.com/kirillzhosul
"""

# Library specific information.
from gatey_sdk.__version__ import (
    __author__,
    __author_email__,
    __copyright__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
)

# Base API.
from gatey_sdk.client import Client
from gatey_sdk.response import Response

__all__ = ["Client", "Response"]
