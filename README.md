# Florgon Gatey SDK for Python (Official).

## This is the official Python SDK for [Florgon Gatey](https://gatey.florgon.space)

## Getting Started

### Install

```
pip install --upgrade gatey-sdk
```

### Configuration

```python
import gatey_sdk
client = gatey_sdk.Client(
    project_id=PROJECT_ID,
    server_secret=PROJECT_SERVER_SECRET,
    client_secret=PROJECT_CLIENT_SECRET,
)
# Notice that you should only enter server or client secret, passing both have no effect as always server will be used.
# (as client not preferred if server secret is passed).
```

### Usage

```python
import gatey_sdk
client = gatey_sdk.Client(
    project_id=PROJECT_ID,
    server_secret=PROJECT_SERVER_SECRET,
)

# Will send message (capture).
client.capture_message("Hello Python Gatey SDK!", level="DEBUG")

# Will capture exception.
@client.catch()
def f():
    raise ValueError

# Same as above.
try:
    raise ValueError
except Exception as e:
    client.capture_exception(e)

# Will work by default also (see Client(handle_global_exceptions=True))
raise ValueError


# (Notice that events by default being sent not immediatly!)
```

## Examples

[See examples directory...](/examples)

## Integrations

[See integrations directory...](/gatey_sdk/integrations) \
[See examples directory...](/examples/integrations)

- [Starlette (FastAPI) integration](/gatey_sdk/integrations/starlette.py)
- [Flask integration](/gatey_sdk/integrations/flask.py)
- Django (TBD)

## Documentation.

[ReadTheDocs](https://gatey-sdk-py.readthedocs.io/) \
[Gatey Documentation](https://florgon.space/dev/gatey)

## License

Licensed under the MIT license, see [`LICENSE`](LICENSE)
