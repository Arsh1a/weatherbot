#!/usr/bin/env python3
"""
Clear portfolio summary — real USDC + live token prices + per-trade breakdown.
Run: python3 summary.py
"""
import json, requests
from pathlib import Path
from datetime import datetime, timezone
from py_clob_client_v2 import ClobClient, SignatureTypeV2, ApiCreds, AssetType, BalanceAllowanceParams
from py_clob_client_v2.constants import POLYGON

cfg      = json.loads(open("secrets.json").read())
creds    = ApiCreds(cfg["clob_api_key"], cfg["clob_api_secret"], cfg["clob_api_passphrase"])
client   = ClobClient("https://clob.polymarket.com", key=cfg["private_key"],
                      chain_id=POLYGON, creds=creds,
                      signature_type=SignatureTypeV2.POLY_1271, funder=cfg["proxy_wallet"])

START    = 100.0
now      = datetime.now(timezone.utc)

# ── Real USDC balance ────────────────────────────────────────────────────────
actual_usdc = int(client.get_balance_allowance(
    BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
)["balance"]) / 1e6

# ── Load all market files ────────────────────────────────────────────────────
markets  = [json.loads(p.read_text()) for p in Path("data/markets").glob("*.json")]
open_pos = [m for m in markets if m.get("position") and m["position"].get("status") == "open"]
closed   = [m for m in markets if m.get("position") and m["position"].get("status") == "closed"
            and m["position"].get("close_reason") != "never_filled"]
resolved = [m for m in markets if m.get("status") == "resolved"
            and m.get("resolved_outcome") not in (None, "no_position")
            and m.get("pnl") is not None]

# ── Fetch live prices for open positions ────────────────────────────────────
def live_bid(market_id):
    try:
        r = requests.get(f"https://gamma-api.polymarket.com/markets/{market_id}", timeout=5)
        d = r.json()
        bid = d.get("bestBid")
        ask = d.get("bestAsk")
        return float(bid) if bid else None, float(ask) if ask else None
    except Exception:
        return None, None

# ── Print ────────────────────────────────────────────────────────────────────
W = 60
print(f"\n{'═'*W}")
print(f"  WEATHERBET  —  PORTFOLIO SUMMARY")
print(f"  {now.strftime('%Y-%m-%d %H:%M UTC')}")
print(f"{'═'*W}")

# CASH
print(f"\n  STARTING CAPITAL   ${START:>8.2f}")
print(f"  USDC IN ACCOUNT    ${actual_usdc:>8.2f}   ({'+'if actual_usdc>=START else ''}{actual_usdc-START:.2f})")

# OPEN POSITIONS
total_cost        = 0.0
total_mkt_value   = 0.0
total_win_payout  = 0.0

print(f"\n{'─'*W}")
print(f"  OPEN POSITIONS ({len(open_pos)})")
print(f"{'─'*W}")
print(f"  {'Market':<22} {'Shares':>6} {'Entry':>6} {'Now':>6} {'Cost':>5} {'Curr Val':>8} {'If WIN':>7} {'If LOSE':>7}")
print(f"  {'-'*22} {'-'*6} {'-'*6} {'-'*6} {'-'*5} {'-'*8} {'-'*7} {'-'*7}")

for m in sorted(open_pos, key=lambda x: x["date"]):
    pos   = m["position"]
    mid   = pos["market_id"]
    bid, ask = live_bid(mid)

    entry  = pos["entry_price"]
    shares = pos["shares"]
    cost   = pos["cost"]
    curr   = bid if bid else entry
    mkt_val = round(curr * shares, 2)
    win_pay = round(shares * 1.0, 2)   # $1/share at resolution
    lose_pay = 0.0

    total_cost       += cost
    total_mkt_value  += mkt_val
    total_win_payout += win_pay

    change = curr - entry
    arrow  = "▲" if change > 0.01 else ("▼" if change < -0.01 else "─")
    label  = f"{m['city_name']} {m['date'][5:]}"

    print(f"  {label:<22} {shares:>6.2f} ${entry:>5.3f} {arrow}${curr:>5.3f} ${cost:>4.2f} ${mkt_val:>7.2f} ${win_pay:>6.2f} ${lose_pay:>6.2f}")

print(f"  {'TOTAL':<22} {'':>6} {'':>6} {'':>6} ${total_cost:>4.2f} ${total_mkt_value:>7.2f} ${total_win_payout:>6.2f}  $0.00")

# CLOSED (stopped/forecast-changed — partial exits)
if closed:
    print(f"\n{'─'*W}")
    print(f"  CLOSED EARLY ({len(closed)})")
    print(f"{'─'*W}")
    for m in sorted(closed, key=lambda x: x["date"]):
        pos    = m["position"]
        pnl    = pos.get("pnl", 0) or 0
        reason = pos.get("close_reason", "?")
        print(f"  {m['city_name']:<16} {m['date']}  {reason:<18}  PnL: {'+'if pnl>=0 else ''}{pnl:.2f}")

# RESOLVED
if resolved:
    print(f"\n{'─'*W}")
    print(f"  RESOLVED MARKETS ({len(resolved)})")
    print(f"{'─'*W}")
    for m in sorted(resolved, key=lambda x: x["date"]):
        outcome = m["resolved_outcome"].upper()
        pnl     = m.get("pnl", 0) or 0
        print(f"  {m['city_name']:<16} {m['date']}  {outcome:<6}  PnL: {'+'if pnl>=0 else ''}{pnl:.2f}")
    resolved_pnl = sum(m.get("pnl", 0) or 0 for m in resolved)
    print(f"  {'Resolved PnL:':<36} {'+'if resolved_pnl>=0 else ''}{resolved_pnl:.2f}")

# BOTTOM LINE
print(f"\n{'═'*W}")
print(f"  BOTTOM LINE")
print(f"{'─'*W}")

cash          = actual_usdc
tokens_now    = total_mkt_value
total_now     = cash + tokens_now
total_if_win  = cash + total_win_payout
total_if_lose = cash + 0

print(f"  Cash (USDC):          ${cash:>8.2f}")
print(f"  Open tokens (at bid): ${tokens_now:>8.2f}   ({len(open_pos)} positions)")
print(f"  ─────────────────────────────")
print(f"  Portfolio now:        ${total_now:>8.2f}   ({'+'if total_now>=START else ''}{total_now-START:.2f} vs $100 start)")
print(f"  If ALL open bets WIN: ${total_if_win:>8.2f}   ({'+'if total_if_win>=START else ''}{total_if_win-START:.2f})")
print(f"  If ALL open bets LOSE:${total_if_lose:>8.2f}   ({'+'if total_if_lose>=START else ''}{total_if_lose-START:.2f})")
print(f"{'═'*W}\n")
