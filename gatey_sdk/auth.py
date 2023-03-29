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

    def request_oauth_from_stdin(self) -> None:
        """
        Get access token from stdin (IO, user).
        """

        print(
            "\tOpen page in browser, signin and copy url here:",
            self.get_manual_oauth_user_login_url(),
            sep="\n\t\t",
        )

        oauth_redirect_uri = input("\tRedirect URI: ")
        oauth_access_token = self.parse_access_token_from_redirect_uri(
            redirect_uri=oauth_redirect_uri
        )

        print(f"\tSuccessfully grabbed access token: {oauth_access_token}")
        self.access_token = oauth_access_token

    @staticmethod
    def get_manual_oauth_user_login_url(
        client_id: int = 1,
        scope: str = "gatey",
        response_type: str = "token",
        redirect_uri: str = "https://florgon.com/oauth/blank",
        oauth_screen_url: str = "https://florgon.com/oauth/authorize",
    ) -> str:
        """
        Returns url for OAuth user login manually.
        """
        return f"{oauth_screen_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type={response_type}"

    @staticmethod
    def parse_access_token_from_redirect_uri(redirect_uri: str) -> Optional[str]:
        """
        Returns token from redirect uri (OAuth) or None if not found there.
        """
        url = redirect_uri.split("#token=")
        return url[1] if len(url) > 1 else None
