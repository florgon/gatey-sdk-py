import gatey_sdk

client = gatey_sdk.Client()
print(client.methods.utils_get_server_time())

t_diff = client.get_server_time_difference()
if t_diff > 10:
    print("Server and client time is too much runs out")
else:
    print("Server and client time is not runs out")
    print(f"Time diff: {t_diff}")
