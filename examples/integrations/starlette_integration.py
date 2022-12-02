import json

from fastapi import FastAPI
from gatey_sdk.integrations.starlette import GateyStarletteMiddleware
from gatey_sdk import Client


def print_transport(event):
    if "exception" in event:
        event["exception"].pop("traceback")
    json_string = json.dumps(
        event,
        indent=2,
        sort_keys=True,
    )
    print(json_string)


# Notice that hooks and transport print may differs because transport is not intended with middleware hooks.
async def pre_capture_hook(*_):
    print("[debug middleware] Pre capture hook...")


async def post_capture_hook(*_):
    print("[debug middleware] Post capture hook...")


async def on_request_hook(*_):
    print("[debug middleware] On request hook...")


app = FastAPI()

client = Client(
    transport=print_transport,
    include_platform_info=False,
    include_runtime_info=False,
    include_sdk_info=False,
    handle_global_exceptions=False,
    exceptions_capture_code_context=False,
)

app.add_middleware(
    GateyStarletteMiddleware,
    client=client,
    capture_requests_info=True,
    client_getter=None,
    capture_exception_options=None,
    capture_reraise_after=False,  # Only for testing!
    pre_capture_hook=pre_capture_hook,
    post_capture_hook=post_capture_hook,
    on_request_hook=on_request_hook,
)


@app.get("/raise")
def app_raise_route():
    return 1 / 0


if __name__ == "__main__":
    from uvicorn import run

    run(app)
