import json, traceback
from pathlib import Path
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, BalanceAllowanceParams, AssetType
from py_clob_client.constants import POLYGON

HOST = "https://clob.polymarket.com"

secrets = json.loads(Path("secrets.json").read_text(encoding="utf-8"))
cfg     = json.loads(Path("config.json").read_text(encoding="utf-8"))
cfg.update(secrets)

creds = ApiCreds(
    api_key=cfg["clob_api_key"],
    api_secret=cfg["clob_api_secret"],
    api_passphrase=cfg["clob_api_passphrase"],
)

client = ClobClient(HOST, key=cfg["private_key"], chain_id=POLYGON, creds=creds,
                    signature_type=0, funder=cfg["wallet_address"])

print("Checking USDC balance & allowance...")
try:
    params = BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    bal = client.get_balance_allowance(params)
    print("  Result:", bal)
except Exception:
    traceback.print_exc()

print("\nSetting USDC allowance...")
try:
    params = BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    resp = client.update_balance_allowance(params)
    print("  Result:", resp)
except Exception:
    traceback.print_exc()
