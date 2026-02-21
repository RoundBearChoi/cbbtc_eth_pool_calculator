from web3 import Web3


class Wallet:
    def __init__(self):
        self.address = None
        self.eth_balance = 0.0
        self.cbbtc_balance = 0.0


    def update_balances(self):
        address_input = input("\nenter your base network wallet address (starts with 0x): ").strip()

        if not address_input.startswith("0x") or len(address_input) != 42:
            print("❌ invalid address format")
            return

        # connect to base (public RPC - fine for personal use)
        w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

        if not w3.is_connected():
            print("❌ could not connect to base network.. try again later.")
            return

        try:
            # convert to checksum address
            self.address = w3.to_checksum_address(address_input)

            print('')
            print(f"🔍 fetching balances..")

            # === eth balance (18 decimals) ===
            eth_wei = w3.eth.get_balance(self.address)
            self.eth_balance = w3.from_wei(eth_wei, "ether")

            # === cbBTC balance (8 decimals) ===
            cbbtc_contract = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"  # official cbBTC on Base
            abi = [{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }]
            contract = w3.eth.contract(address=w3.to_checksum_address(cbbtc_contract), abi=abi)
            raw_balance = contract.functions.balanceOf(self.address).call()
            self.cbbtc_balance = raw_balance / 10**8

            print("\n✅ current balance")
            print(f"   eth   : {self.eth_balance:.6f}")
            print(f"   cbbtc : {self.cbbtc_balance:.8f}")

        except Exception as e:
            print(f"❌ error: {e}")


    def __str__(self):
        return (f"wallet({self.address})\n"
                f"eth   : {self.eth_balance:.6f}\n"
                f"cbbtc : {self.cbbtc_balance:.8f}")


if __name__ == "__main__":
    wallet = Wallet()
    wallet.update_balances()
