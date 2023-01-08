"""
    Flask integration(s).
"""

from typing import Callable, Dict, Any, Optional
from werkzeug.wrappers import Request
from flask import abort
from gatey_sdk.client import Client

# Type aliases for callables.
HookCallable = Callable[["GateyFlaskMiddleware", Dict, Callable], None]
ClientGetterCallable = Callable[[], Client]


class GateyFlaskMiddleware:
    """Gatey SDK Starlette middleware."""

    # Requirements.
    flask_app: Callable[[Dict, Callable], Any]
    gatey_client: Client

    # Gatey options.
    capture_exception_options: Dict[str, Any] = {"include_default_tags": True}
    pre_capture_hook: HookCallable
    post_capture_hook: HookCallable
    client_getter: ClientGetterCallable
    capture_requests_info: bool = False
    capture_requests_info_additional_tags: Dict[str, str] = dict()

    def __init__(
        self,
        app,
        client: Optional[Client] = None,
        *,
        capture_requests_info: bool = False,
        client_getter: Optional[ClientGetterCallable] = None,
        capture_exception_options: Optional[Dict[str, Any]] = None,
        pre_capture_hook: Optional[HookCallable] = None,
        post_capture_hook: Optional[HookCallable] = None,
        on_request_hook: Optional[HookCallable] = None,
        capture_requests_info_additional_tags: Optional[Dict[str, str]] = None,
    ) -> None:
        self.flask_app = app
        self.gatey_client = client  # Redefined below by `client_getter`.

        self.capture_requests_info = capture_requests_info
        self.capture_exception_options = (
            capture_exception_options
            if capture_exception_options
            else self.capture_exception_options
        )
        self.capture_requests_info_additional_tags = (
            capture_requests_info_additional_tags
            if capture_requests_info_additional_tags
            else dict()
        )
        self.client_getter = (
            client_getter if client_getter else self._default_client_getter
        )

        # Hooks.
        hooks = {
            "pre_capture_hook": pre_capture_hook,
            "post_capture_hook": post_capture_hook,
            "on_request_hook": on_request_hook,
        }
        for name, hook in hooks.items():
            setattr(self, name, hook or self._default_void_hook)

        self.gatey_client = self.client_getter()
        if not isinstance(self.gatey_client, Client):
            raise ValueError(
                "Gatey client is invalid! Please review `client` param or review your client getter!"
            )

    def __call__(self, environ: Dict, start_response: Callable) -> None:
        """
        Middleware itself (handle request).
        """
        return self._execute_app_wrapped(environ, start_response)

    def _execute_app_wrapped(self, environ: Dict, start_response: Callable) -> Any:
        """
        Executes app wrapped with middleware.
        """
        app_args = [environ, start_response]

        if self.on_request_hook:
            self.on_request_hook(self, *app_args)

        if self.capture_requests_info:
            self._capture_request_info(environ=environ)

        try:
            return self.flask_app(*app_args)
        except Exception as _flask_app_exception:
            client = self.client_getter()
            if client and isinstance(client, Client):
                self.pre_capture_hook(self, *app_args)

                capture_options = self.capture_exception_options.copy()
                if "tags" not in capture_options:
                    capture_options["tags"] = self._get_request_tags_from_environ(
                        environ=environ
                    )

                client.capture_exception(_flask_app_exception, **capture_options)

                self.post_capture_hook(self, *app_args)
            abort(500)

    @staticmethod
    def _get_request_tags_from_environ(environ: Dict) -> Dict[str, str]:
        """
        Returns tags for request from request environ.
        """
        request = Request(environ)
        return {
            "query": request.query_string.decode("utf-8"),
            "path": request.root_path + request.path,
            "scheme": request.scheme,
            "method": request.method,
            "client_host": request.remote_addr,
            "server_host": ":".join(map(str, request.server)),
        }

    def _capture_request_info(self, environ: Dict) -> None:
        """
        Captures request info as message to the client.
        """
        client = self.client_getter()
        if not client:
            return

        tags = self._get_request_tags_from_environ(environ=environ)
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
