import json
import gatey_sdk


def print_transport(event):
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
    client.capture_exception(e, _level="ERROR")
