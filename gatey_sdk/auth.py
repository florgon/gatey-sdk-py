"""
    NOT REFACTORED.
    NOT USED.
"""

from urllib.parse import urlparse
from urllib.parse import parse_qs


class Auth:
    def _parse_access_token_from_redirect_uri(self, redirect_uri: str) -> str:
        """
        Parse access token from OAuth redirect URI where user was redirected.
        """
        parsed_url = urlparse(url=redirect_uri)
        access_token = parse_qs(parsed_url.query).get("access_token", None)
        if access_token:
            return access_token[0]
        return ""
