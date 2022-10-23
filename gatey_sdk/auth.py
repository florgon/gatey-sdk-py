"""
    NOT REFACTORED.
    NOT USED.
"""

from typing import Optional
# from urllib.parse import urlparse
# from urllib.parse import parse_qs


class Auth:
    """
    Wrapper for authentication data (access token, project information for capturing (project id, client / server secret))
    """

    # Access token is used for user authorized calls.
    # Like editing project, or interacting with administration tools.
    access_token: Optional[str] = None

    # Project information for capturing events.
    # Secrets is used to verify calls to the project event capturer.
    project_id: Optional[int] = None
    server_secret: Optional[str] = None
    client_secret: Optional[str] = None

    def __init__(
        self,
        access_token: Optional[str] = None,
        project_id: Optional[int] = None,
        server_secret: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        :param access_token: Access token of the your account with `gatey` scope.
        :param project_id: Project id to capture event for.
        :param server_secret: Secret of the project.
        :param client_secret: Secret of the project.
        """
        self.access_token = access_token
        self.project_id = project_id
        self.server_secret = server_secret
        self.client_secret = client_secret

    # def _parse_access_token_from_redirect_uri(self, redirect_uri: str) -> str:
    #    """
    #    Parse access token from OAuth redirect URI where user was redirected.
    #    """
    #    parsed_url = urlparse(url=redirect_uri)
    #    access_token = parse_qs(parsed_url.query).get("access_token", None)
    #    if access_token:
    #        return access_token[0]
    #    return ""
