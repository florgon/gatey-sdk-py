import gatey_sdk

client = gatey_sdk.Client()
client.change_api_provider("https://api.florgon.space/gatey")  # DEFAULT.

print(client.method("utils.getServerTime"))
print(client.method("utils.getServerTime", my_var="get_param"))

t_diff = client.get_server_time_difference()
if t_diff > 10:
    print("Server and client time is too much runs out")
else:
    print("Server and client time is not runs out")
    print(f"Time diff: {t_diff}")
