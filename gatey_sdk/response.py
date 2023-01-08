"""
    Response class.
    Result of all API methods.
    Implements Gatey API response structure (For success).
    
    If API request will raise error, there will be `gatey_sdk.exceptions.GateyApiError`
"""

from typing import Dict, Any, Optional
from requests import Response as _HttpResponse


class Response:
    """
    Gatey API response structure.
    """

    # Raw response fields.
    _raw_json: Optional[Dict] = None
    _raw_response: Optional[_HttpResponse] = None

    # API response fields.
    _response_version: Optional[str] = None
    _response_object: Optional[Dict] = None  # `success` response field.

    def __init__(self, http_response: _HttpResponse):
        """
        :param http_response: Response object (HTTP).
        """

        # Store raw response to work later.
        self._raw_response = http_response

        # Parse raw response once for working later.
        self._raw_json = self._raw_response.json()
        self._response_object = self._raw_json.get("success", dict())
        self._response_version = self._raw_json.get("v", "-")

    def get(self, key: str, default: Any = None):
        """
        Allows to access Response fields by `response.get(field, default)`.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key: str) -> Any:
        """
        Allows to access Response fields by `response[field]`.
        Notice that this will fall with `KeyError` if field was not found in the response.
        """
        if key not in self._response_object:
            raise KeyError(f"{key} does not exist in the response!")
        field_value = self._response_object.get(key)
        return field_value

    def __getattr__(self, attribute_name: str) -> Any:
        """
        Allows to access Response fields by `response.my_response_var`.
        Notice that this will fall with `AttributeError` if field was not found in the response.
        """
        if attribute_name not in self._response_object:
            raise AttributeError(f"{attribute_name} does not exist in the response!")
        attribute_value = self._response_object.get(attribute_name)
        return attribute_value

    def get_version(self) -> str:
        """
        Returns response API version.
        """
        return self._response_version

    def get_response_object(self) -> Dict:
        """
        Returns response object.
        """
        return self._response_object

    def raw_json(self) -> Dict:
        """
        Returns raw JSON from the response.
        WARNING: Do not use this method.
        """
        return self._raw_json

    def raw_response(self) -> _HttpResponse:
        """
        Returns raw response object.
        WARNING: Do not use this method.
        """
        return self._raw_response
