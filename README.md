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
client = gatey_sdk.Client()
```

### Usage

```python
import gatey_sdk
client = gatey_sdk.Client(project_id=PROJECT_ID, server_secret=PROJECT_SECRET)

# Will send message (capture).
client.capture_message("Hello Python Gatey SDK!", level="DEBUG")

# Will capture exception.
@client.catch
def f():
    raise ValueError

# Same as above.
try:
    raise ValueError
except Exception as e:
    client.capture_exception(e)
```

## Integrations

For now there is no native integrations.

## Documentation.

[ReadTheDocs](https://gatey-sdk-py.readthedocs.io/) \
[Gatey Documentation](https://florgon.space/dev/gatey)

## License

Licensed under the MIT license, see [`LICENSE`](LICENSE)
