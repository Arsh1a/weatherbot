from py_clob_client_v2 import ClobClient, SignatureTypeV2, ApiCreds, OrderArgs, OrderType
from py_clob_client_v2.constants import POLYGON

HOST = "https://clob.polymarket.com"


def get_client(cfg):
    creds = ApiCreds(
        api_key=cfg["clob_api_key"],
        api_secret=cfg["clob_api_secret"],
        api_passphrase=cfg["clob_api_passphrase"],
    )
    return ClobClient(HOST, key=cfg["private_key"], chain_id=POLYGON, creds=creds,
                      signature_type=SignatureTypeV2.POLY_1271, funder=cfg["proxy_wallet"])


def place_buy(client, token_id, price, usdc_size):
    price  = round(price, 2)
    shares = round(usdc_size / price, 2)
    order  = client.create_order(OrderArgs(token_id=token_id, price=price, size=shares, side="BUY"))
    return client.post_order(order, OrderType.GTC)


def place_sell(client, token_id, price, shares):
    price = round(price, 2)
    order = client.create_order(OrderArgs(token_id=token_id, price=price, size=shares, side="SELL"))
    return client.post_order(order, OrderType.GTC)
