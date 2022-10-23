import gatey_sdk

client = gatey_sdk.Client(project_id=-1, check_api_auth_on_init=False)
print("Auth check: ", client.api.do_auth_check()) # Soft auth check (hard: do_hard_auth_check())