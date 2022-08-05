"""
    Exceptions is being captured.
"""
import gatey_sdk

client = gatey_sdk.Client()


# raise ValueError


@client.catch(
    reraise=False,
    exception=BaseException,
    ignored_exceptions=[],
)
def test_wrapped():
    print("Message before exception fire")
    raise TypeError
    print("Message after exception fire")


# try:
#    raise ValueError
# except Exception as e:
#    client.capture_exception(e)

test_wrapped()
