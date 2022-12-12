import gatey_sdk


def print_transport(event):
    """
    No gatey_sdk.PrintTransport for formatted print.
    """
    context = event["exception"]["traceback"][-1]["context"]
    print("---------------------")
    print("Code context sent to server: ")
    print("---------------------")
    print(*context["pre"], sep="\n")
    print(context["target"], "[TARGET_LINE]")
    print(*context["post"], sep="\n")
    print("---------------------")


client = gatey_sdk.Client(transport=print_transport)

try:
    raise ValueError("Message text!")
except Exception as e:
    client.capture_exception(e, level="error")
