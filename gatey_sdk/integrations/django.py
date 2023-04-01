# pylint: disable=inconsistent-return-statements
"""
    Django integration(s).
"""


from typing import Dict, Callable, Any

from gatey_sdk.client import Client
from django.http import HttpRequest
from django.conf import settings

# Type aliases for callables.
HookCallable = Callable[["GateyDjangoMiddleware", HttpRequest, Callable], None]
CaptureHookCallable = Callable[
    ["GateyDjangoMiddleware", HttpRequest, BaseException], None
]
ClientGetterCallable = Callable[[], Client]


class GateyDjangoMiddleware:
    """Gatey SDK Django middleware."""

    # Requirements.
    get_response: Callable[[HttpRequest], Any]
    gatey_client: Client

    # Gatey options.
    capture_exception_options: Dict[str, Any] = {"include_default_tags": True}
    pre_capture_hook: CaptureHookCallable
    post_capture_hook: CaptureHookCallable
    on_request_hook: HookCallable
    client_getter: ClientGetterCallable
    capture_requests_info: bool = False
    capture_requests_info_additional_tags: Dict[str, str] = dict()

    def __init__(self, get_response: Callable[[HttpRequest], Any]) -> None:
        # Django middleware getter.
        self.get_response = get_response

        self.gatey_client = getattr(
            settings, "GATEY_CLIENT", None
        )  # Redefined below by `client_getter`.

        self.capture_requests_info = getattr(
            settings, "GATEY_CAPTURE_REQUESTS_INFO", None
        )

        self.capture_exception_options = getattr(
            settings, "GATEY_CAPTURE_EXCEPTION_OPTIONS", self.capture_exception_options
        )

        self.capture_requests_info_additional_tags = getattr(
            settings, "GATEY_CAPTURE_REQUESTS_INFO_ADDITIONAL_TAGS", dict()
        )

        self.client_getter = getattr(
            settings, "GATEY_CLIENT_GETTER", self._default_client_getter
        )

        # Hooks.
        hooks = {
            "pre_capture_hook": getattr(
                settings, "GATEY_PRE_CAPTURE_HOOK", self._default_void_hook
            ),
            "post_capture_hook": getattr(
                settings, "GATEY_POST_CAPTURE_HOOK", self._default_void_hook
            ),
            "on_request_hook": getattr(
                settings, "GATEY_ON_REQUEST_HOOK", self._default_void_hook
            ),
        }
        for name, hook in hooks.items():
            setattr(self, name, hook)

        self.gatey_client = self.client_getter()
        if not isinstance(self.gatey_client, Client):
            raise ValueError(
                "Gatey client is invalid! Please review `client` param or review your client getter!"
            )

    def __call__(self, request: HttpRequest):
        """
        Middleware itself (handle request).
        """

        if self.on_request_hook:
            self.on_request_hook(self, request, self.get_response)

        if self.capture_requests_info:
            self._capture_request_info(request=request)

        return self.get_response(request)

    def process_exception(self, request, exception):
        """
        Process exception by capturing it via Gatey Client.
        """

        client = self.client_getter()
        if client and isinstance(client, Client):
            self.pre_capture_hook(self, request, exception)

            capture_options = self.capture_exception_options.copy()
            if "tags" not in capture_options:
                capture_options["tags"] = self._get_request_tags_from_request(
                    request=request
                )

            client.capture_exception(exception, **capture_options)

            self.post_capture_hook(self, request, exception)
        return None

    @staticmethod
    def _get_request_tags_from_request(request: HttpRequest) -> Dict[str, str]:
        """
        Returns tags for request from request.
        """
        return {
            "gatey.sdk.integration_type": "Django",
            "method": request.method,
            "scheme": request.scheme,
            "port": request.get_port(),
            "path": request.path,
            "full_path": request.get_full_path(),
            "server_host": request.get_host(),
            "client_host": request.META.get("REMOTE_ADDR"),
            "query": request.META["QUERY_STRING"],
            "server_proto": request.META["SERVER_PROTOCOL"],
            "server_soft": request.META["SERVER_SOFTWARE"],
            "content_type": request.META["CONTENT_TYPE"],
            "http_upgrade_insecure_requests": request.META[
                "HTTP_UPGRADE_INSECURE_REQUESTS"
            ],
            "http_ua_platform": request.META["HTTP_SEC_CH_UA_PLATFORM"],
            "http_ua_mobile": request.META["HTTP_SEC_CH_UA_MOBILE"],
            "http_connection": request.META["HTTP_CONNECTION"],
        }

    def _capture_request_info(self, request: HttpRequest) -> None:
        """
        Captures request info as message to the client.
        """
        client = self.client_getter()
        if not client:
            return

        tags = self._get_request_tags_from_request(request=request)
        message = f"{tags['method']} '{tags['path']}'"
        message = message if message != " ''" else "Request was handled."
        tags.update(self.capture_requests_info_additional_tags)

        client.capture_message(
            message,
            level="debug",
            tags=tags,
        )

    def _default_client_getter(self) -> Client:
        """
        Default getter for Gatey client if none is specified.
        """
        return self.gatey_client

    @staticmethod
    def _default_void_hook(*_) -> None:
        """
        Default hook for pre/post capture, just does nohing.
        """
        return None
