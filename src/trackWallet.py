from web3 import Web3
import requests
from datetime import datetime, timedelta, timezone

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

            self.eth_balance = w3.from_wei(w3.eth.get_balance(self.address), "ether")

            cbbtc_contract = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"
            abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
            contract = w3.eth.contract(address=w3.to_checksum_address(cbbtc_contract), abi=abi)
            self.cbbtc_balance = contract.functions.balanceOf(self.address).call() / 10**8

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

        tx_list = []
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
                        typ = "cbBTC"
                        label = "cbBTC Transfer"
                    else:
                        value = int(tx.get("value", 0)) / 10**18
                        typ = "ETH"
                        if action == "txlistinternal" and value < 0.000001:
                            continue
                        to_addr = tx.get("to", "").lower()
                        if any(p in to_addr for p in ["46a15b0b", "c6a2db66"]):
                            label = "🥞 Pancake V3 LP"
                        else:
                            label = "Internal ETH" if action == "txlistinternal" else ("ETH Transfer" if value > 0.000001 else "Contract Call")

                    direction = "OUT" if tx.get("from", "").lower() == lower_addr else "IN"

                    tx_list.append({
                        "time": datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                        "dir": direction,
                        "amount": value,
                        "label": label,
                        "type": typ
                    })
            except Exception as e:
                print(f"   ⚠️ {action} error: {e}")

        if not tx_list:
            print("\n   No ETH or cbBTC activity in the last 48 hours.")
            self.print_current_balance()
            return

        # Dedupe + sort OLDEST → NEWEST
        tx_list = list({(t["time"], t["amount"], t["label"]): t for t in tx_list}.values())
        tx_list.sort(key=lambda x: x["time"])

        print(f"\n✅ {len(tx_list)} ETH & cbBTC activities found (oldest → newest):\n")
        for t in tx_list:
            amt_str = f"{t['amount']:.6f} ETH" if t["type"] == "ETH" else f"{t['amount']:.8f} cbBTC"
            print(f"{t['time']}  |  {t['dir']:>3}  {amt_str:>18}  |  {t['label']}")

        # Current balance at the very end
        self.print_current_balance()

    def print_current_balance(self):
        print("\n" + "="*70)
        print("✅ CURRENT BALANCE (after all listed activity)")
        print("="*70)
        print(f"   eth   : {self.eth_balance:.6f}")
        print(f"   cbbtc : {self.cbbtc_balance:.8f}")
        print("="*70)

if __name__ == "__main__":
    wallet = Wallet()
    if wallet.update_balances():
        wallet.get_eth_cbbtc_activity(48)
