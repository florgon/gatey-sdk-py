import gatey_sdk

client = gatey_sdk.Client()


@client.catch(reraise=False, exception=BaseException, ignored_exceptions=[])
def f():
    print("before exc")
    raise ValueError
    print("after exc")


f()
