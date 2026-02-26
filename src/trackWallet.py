from web3 import Web3
import requests
from datetime import datetime, timedelta, timezone
import csv
import os

class Wallet:
    def __init__(self):
        self.address = None
        self.eth_balance = 0.0
        self.cbbtc_balance = 0.0

    def update_balances(self) -> bool:
        address_input = input("\nenter your base network wallet address (starts with 0x): ").strip()
        if not address_input.startswith("0x") or len(address_input) != 42:
            print("❌ invalid address format")
            return False

        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        if not w3.is_connected():
            print("❌ could not connect..")
            return False

        try:
            self.address = w3.to_checksum_address(address_input)
            print("\n🔄 fetching balances..")

            # ← FIXED: convert Decimal → float for easy math
            self.eth_balance = float(w3.from_wei(w3.eth.get_balance(self.address), "ether"))

            cbbtc_contract = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"
            abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
            contract = w3.eth.contract(address=w3.to_checksum_address(cbbtc_contract), abi=abi)
            raw_balance = contract.functions.balanceOf(self.address).call()
            self.cbbtc_balance = float(raw_balance) / 10**8

            return True
        except Exception as e:
            print(f"❌ {e}")
            return False

    def get_eth_cbbtc_activity(self, hours: int = 48):
        if not self.address:
            print("❌ run update_balances first")
            return

        cutoff = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp())
        url = "https://base.blockscout.com/api"
        print(f"\n🔍 fetching ALL ETH + cbBTC activity (last {hours}h)...")

        raw_tx = []
        lower_addr = self.address.lower()

        for action in ["txlist", "txlistinternal", "tokentx"]:
            params = {
                "module": "account",
                "action": action,
                "address": self.address,
                "offset": "1000",
                "sort": "desc"
            }
            if action == "tokentx":
                params["contractaddress"] = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"

            try:
                r = requests.get(url, params=params, timeout=15).json()
                results = r.get("result", [])
                print(f"   [DEBUG] {action}: {len(results)} records found")

                for tx in results:
                    ts = int(tx.get("timeStamp", 0))
                    if ts < cutoff:
                        break

                    if action == "tokentx":
                        value = int(tx["value"]) / 10**8
                        token = "cbBTC"
                        label = "cbBTC Transfer"
                    else:
                        value = int(tx.get("value", 0)) / 10**18
                        token = "ETH"
                        if action == "txlistinternal" and value < 0.00000001:
                            continue
                        to_addr = tx.get("to", "").lower()
                        if any(p in to_addr for p in ["46a15b0b", "c6a2db66"]):
                            label = "🥞 Pancake V3 LP"
                        else:
                            label = "Internal ETH" if action == "txlistinternal" else ("ETH Transfer" if value > 0.000001 else "Contract Call")

                    direction = "OUT" if tx.get("from", "").lower() == lower_addr else "IN"

                    raw_tx.append({
                        "time": datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                        "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                        "time_only": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
                        "dir": direction,
                        "amount": value,
                        "token": token,
                        "label": label,
                        "timestamp": ts
                    })
            except Exception as e:
                print(f"   ⚠️ {action} error: {e}")

        if not raw_tx:
            print("\n   No ETH or cbBTC activity in the last 48 hours.")
            self.print_current_balance()
            return

        # Dedupe + sort OLDEST → NEWEST
        tx_list = list({t["time"]: t for t in raw_tx}.values())
        tx_list.sort(key=lambda x: x["timestamp"])

        # === Calculate balance AFTER each transaction (starting from current balance) ===
        current_eth = self.eth_balance
        current_cbbtc = self.cbbtc_balance

        for tx in reversed(tx_list):
            tx['balance_eth_after'] = current_eth
            tx['balance_cbbtc_after'] = current_cbbtc

            # Undo this transaction to get previous balance
            if tx['dir'] == "OUT":
                if tx['token'] == "ETH":
                    current_eth += tx['amount']
                else:
                    current_cbbtc += tx['amount']
            else:  # IN
                if tx['token'] == "ETH":
                    current_eth -= tx['amount']
                else:
                    current_cbbtc -= tx['amount']

        # === Nice console print ===
        print(f"\n✅ {len(tx_list)} activities found (oldest → newest):\n")
        for t in tx_list:
            amt_str = f"{t['amount']:.8f}"
            print(f"{t['time']}  |  {t['dir']:>3}   {amt_str:>18}  |  {t['token']:>6}  |  {t['label']}")

        self.print_current_balance()

        # === CSV EXPORT ===
        self.export_to_csv(tx_list)

    def print_current_balance(self):
        print("\n" + "="*90)
        print("✅ CURRENT BALANCE")
        print("="*90)
        print(f"   eth   : {self.eth_balance:.8f}")
        print(f"   cbbtc : {self.cbbtc_balance:.8f}")
        print("="*90)

    def export_to_csv(self, tx_list):
        short_addr = self.address[:8] + "..." + self.address[-6:]
        filename = f"transactions_{short_addr}_last48h.csv"

        headers = ["date", "time", "bound", "cbbtc_amount", "eth_amount", "balance_cbbtc_after", "balance_eth_after", "label"]

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for t in tx_list:
                row = [
                    t['date'],
                    t['time_only'],
                    t['dir'],
                    round(t['amount'], 8) if t['token'] == "cbBTC" else 0.00000000,
                    round(t['amount'], 8) if t['token'] == "ETH" else 0.00000000,
                    round(t['balance_cbbtc_after'], 8),
                    round(t['balance_eth_after'], 8),
                    t['label']
                ]
                writer.writerow(row)

        print(f"\n💾 CSV saved → **{filename}**")
        print(f"   Full path: {os.path.abspath(filename)}")

if __name__ == "__main__":
    wallet = Wallet()
    if wallet.update_balances():
        wallet.get_eth_cbbtc_activity(48)
