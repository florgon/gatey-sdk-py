from flask import Flask
from gatey_sdk.integrations.flask import GateyFlaskMiddleware
from gatey_sdk import Client, PrintTransport


# Notice that hooks and transport print may differs because transport is not intended with middleware hooks.
def pre_capture_hook(*_):
    print("[debug middleware] Pre capture hook...")


def post_capture_hook(*_):
    print("[debug middleware] Post capture hook...")


def on_request_hook(*_):
    print("[debug middleware] On request hook...")


app = Flask(__name__)

client = Client(
    transport=PrintTransport(
        prepare_event=lambda e: (e, e.get("exception", {}).pop("traceback", None))[0]
    ),
    include_platform_info=False,
    include_runtime_info=False,
    include_sdk_info=False,
    handle_global_exceptions=False,
    exceptions_capture_code_context=False,
)
app.wsgi_app = GateyFlaskMiddleware(
    app.wsgi_app,
    client=client,
    capture_requests_info=True,
    client_getter=None,
    capture_exception_options=None,
    pre_capture_hook=pre_capture_hook,
    post_capture_hook=post_capture_hook,
    on_request_hook=on_request_hook,
)


@app.get("/raise")
def app_raise_route():
    return 1 / 0


if __name__ == "__main__":
    app.run("127.0.0.1", "8000", debug=True)
