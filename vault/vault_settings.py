import os

import hvac

VAULT_HOSTNAME = os.getenv("VAULT_HOSTNAME")
VAULT_PORT = os.getenv("VAULT_PORT")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

client = hvac.Client(
    url=f"{VAULT_HOSTNAME}:{VAULT_PORT}",
    token=VAULT_TOKEN,
)

if not client.is_authenticated():
    raise RuntimeError("Vault not authenticated.")

vault_settings = client.secrets.kv.read_secret(path="app", mount_point="bot")
for key, value in vault_settings["data"]["data"].items():
    os.environ[key] = str(value)
