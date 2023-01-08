"""
    Starlette integration(s).
"""

from typing import Callable, Dict, Any, Optional, Awaitable

from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.datastructures import Headers

from gatey_sdk.client import Client

# Type aliases for callables.
HookCallable = Callable[
    ["GateyStarletteMiddleware", Scope, Receive, Send], Awaitable[None]
]
ClientGetterCallable = Callable[[], Client]


class GateyStarletteMiddleware:
    """Gatey SDK Starlette middleware."""

    # Requirements.
    starlette_app: ASGIApp
    gatey_client: Client

    # Gatey options.
    capture_exception_options: Dict[str, Any] = {"include_default_tags": True}
    pre_capture_hook: HookCallable
    post_capture_hook: HookCallable
    on_request_hook: HookCallable
    client_getter: ClientGetterCallable
    capture_reraise_after: bool = True
    capture_requests_info: bool = False
    capture_requests_info_additional_tags: Dict[str, str] = dict()

    def __init__(
        self,
        app: ASGIApp,
        client: Optional[Client] = None,
        *,
        capture_requests_info: bool = False,
        client_getter: Optional[ClientGetterCallable] = None,
        capture_exception_options: Optional[Dict[str, Any]] = None,
        capture_reraise_after: bool = True,
        pre_capture_hook: Optional[HookCallable] = None,
        post_capture_hook: Optional[HookCallable] = None,
        on_request_hook: Optional[HookCallable] = None,
        capture_requests_info_additional_tags: Optional[Dict[str, str]] = None,
    ) -> None:
        self.starlette_app = app
        self.gatey_client = client  # Redefined below by `client_getter`.

        self.capture_reraise_after = capture_reraise_after
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

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Middleware itself (handle request).
        """
        if scope["type"] != "http":
            # Skip non-requests (like, lifespan event).
            # Do not have there `simple_response`.
            await self.starlette_app(scope, receive, send)
            return
        await self._execute_app_wrapped(scope, receive, send)

    async def _execute_app_wrapped(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """
        Executes app wrapped with middleware.
        """
        app_args = [scope, receive, send]

        if self.on_request_hook:
            await self.on_request_hook(self, *app_args)

        if self.capture_requests_info:
            await self._capture_request_info(*app_args)

        try:
            await self.starlette_app(*app_args)
        except Exception as _starlette_app_exception:
            client = self.client_getter()
            if client and isinstance(client, Client):
                await self.pre_capture_hook(self, *app_args)

                capture_options = self.capture_exception_options.copy()
                if "tags" not in capture_options:
                    capture_options["tags"] = self._get_request_tags_from_scope(
                        scope=scope
                    )

                client.capture_exception(_starlette_app_exception, **capture_options)

                await self.post_capture_hook(self, *app_args)

            if self.capture_reraise_after:
                raise _starlette_app_exception

    def _get_request_tags_from_scope(self, scope: Scope) -> Dict[str, str]:
        """
        Returns tags for request from request scope.
        """
        query, path, method = (
            scope.get("query_string", b"").decode("UTF-8"),
            scope.get("path", ""),
            scope.get("method", "UNKNOWN"),
        )
        return {
            "query": query,
            "path": path,
            "method": method,
            "client_host": self._get_client_host_from_scope(scope),
            "server_host": ":".join(map(str, scope["server"])),
        }

    async def _capture_request_info(self, scope: Scope, *_) -> None:
        """
        Captures request info as message to the client.
        """
        client = self.client_getter()
        if not client:
            return

        tags = self._get_request_tags_from_scope(scope=scope)
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
    async def _default_void_hook(*_) -> None:
        """
        Default hook for pre/post capture, just does nohing.
        """
        return None

    @staticmethod
    def _get_client_host_from_scope(scope: Scope) -> str:
        """Returns client host (IP) from passed scope, if it is forwarded, queries correct host."""
        header_x_forwarded_for = Headers(scope=scope).get("X-Forwarded-For")
        if header_x_forwarded_for:
            return header_x_forwarded_for.split(",")[0]
        return scope["client"][0]
