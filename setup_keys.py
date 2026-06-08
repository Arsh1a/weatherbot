import json
from pathlib import Path
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

HOST = "https://clob.polymarket.com"


def main():
    secrets_path = Path("secrets.json")
    if not secrets_path.exists():
        print("secrets.json not found — copy secrets.example.json to secrets.json first.")
        return
    secrets = json.loads(secrets_path.read_text(encoding="utf-8"))
    pk = secrets.get("private_key", "")
    proxy = secrets.get("proxy_wallet", "")
    if not pk or "YOUR" in pk.upper():
        print("Add your wallet private_key to secrets.json first.")
        return
    if not proxy or "YOUR" in proxy.upper():
        print("Add your proxy_wallet address to secrets.json first.")
        return
    print(f"EOA:          {secrets['wallet_address']}")
    print(f"Proxy wallet: {proxy}")
    print("Connecting to Polymarket CLOB...")
    # signature_type=2 = POLY_PROXY: EOA signs on behalf of proxy wallet
    client = ClobClient(HOST, key=pk, chain_id=POLYGON,
                        signature_type=2, funder=proxy)
    creds = client.create_or_derive_api_creds()
    secrets = json.loads(secrets_path.read_text(encoding="utf-8"))
    secrets["clob_api_key"]        = creds.api_key
    secrets["clob_api_secret"]     = creds.api_secret
    secrets["clob_api_passphrase"] = creds.api_passphrase
    secrets_path.write_text(json.dumps(secrets, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Done — API key: {creds.api_key[:12]}...")
    print('Now set "live_trading": true in config.json to enable real trades.')


if __name__ == "__main__":
    main()
