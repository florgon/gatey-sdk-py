"""
    Florgon Gatey SDK.

    SDK Library for Florgon Gatey API.
    Provides interface for working with Florgon Gatey.

    Florgon Gatey is a error logging service.
    Library provides interface for working with exceptions, catching them,
    Working with message / events and all another analytics stuff,
    Also there is base API interface,
    allowing to work with native API,
    not base gateway end-user API.

    Author: Florgon Solutions.
    Gatey website: https://gatey.florgon.com/
    Gatey API endpoint: https://api.florgon.com/gatey/
    Gatey developer documentation: https://gatey-sdk-py.readthedocs.io/

    If you have any questions please reach out us at:
    - support@florgon.com

    Main SDK maintainer:
    - Kirill Zhosul (@kirillzhosul)
    - kirillzhosul@florgon.com
    - https://github.com/kirillzhosul
"""

from gatey_sdk.transports import (
    VoidTransport,
    PrintTransport,
    HttpTransport,
    FuncTransport,
    BaseTransport,
)
from gatey_sdk.response import Response

# Internal exceptions.
from gatey_sdk.exceptions import GateyTransportError, GateyApiError

# Base API.
from gatey_sdk.client import Client

# Additional API.
from gatey_sdk.api import Api

# Library specific information.
from gatey_sdk.__version__ import (
    __version__,
    __url__,
    __title__,
    __license__,
    __description__,
    __copyright__,
    __author_email__,
    __author__,
)

__all__ = [
    "Client",
    "Response",
    "Api",
    "BaseTransport",
    "HttpTransport",
    "FuncTransport",
    "VoidTransport",
    "PrintTransport",
    "GateyApiError",
    "GateyTransportError",
]
