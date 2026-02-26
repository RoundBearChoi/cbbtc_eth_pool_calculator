from web3 import Web3
import sys

class WalletTracker:
    # ================== CONSTANTS ==================
    CBTC_ADDRESS = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"
    CBTC_ABI = [{
        "constant": True,
        "inputs": [{"name": "who", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }]
    CBTC_DECIMALS = 8
    BLOCKS_PER_DAY = 43200  # Base ~2s block time

    def __init__(self, wallet_address: str, days_ago: int, api_key: str):
        """Initialize tracker with all setup (exactly as original)."""
        self.wallet_address_input = wallet_address.strip()
        self.days_ago = days_ago
        self.api_key = api_key.strip()

        # ================== SETUP ==================
        self.RPC_URL = f"https://base-mainnet.g.alchemy.com/v2/{self.api_key}"
        self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))

        if not self.web3.is_connected():
            print("❌ Failed to connect to Base network")
            sys.exit(1)

        self.wallet_address = self.web3.to_checksum_address(self.wallet_address_input)

        self.cbtc_address = self.web3.to_checksum_address(self.CBTC_ADDRESS)
        self.contract = self.web3.eth.contract(
            address=self.cbtc_address,
            abi=self.CBTC_ABI
        )

        # Block calculation (same logic)
        self.current_block = self.web3.eth.block_number
        self.target_block = max(1, self.current_block - (self.days_ago * self.BLOCKS_PER_DAY))

    def track(self):
        """Run the full balance tracking with identical output to original script."""
        print(f"\n📍 Current block : {self.current_block:,}")
        print(f"📍 Target block (~{self.days_ago} days ago): {self.target_block:,}\n")

        # ================== CURRENT BALANCES ==================
        print("🔄 Fetching CURRENT balances...\n")

        current_eth = self.web3.eth.get_balance(self.wallet_address)
        print(f"ETH   : {self.web3.from_wei(current_eth, 'ether'):.6f} ETH")

        try:
            current_cbbtc = self.contract.functions.balanceOf(self.wallet_address).call()
            print(f"cbBTC : {current_cbbtc / (10 ** self.CBTC_DECIMALS):.8f} cbBTC")
        except Exception as e:
            print(f"❌ Error fetching current cbBTC: {e}")

        # ================== PAST BALANCES ==================
        print(f"\n🔄 Fetching balances ~{self.days_ago} day(s) ago (block {self.target_block})...\n")

        past_eth = self.web3.eth.get_balance(self.wallet_address, block_identifier=self.target_block)
        print(f"ETH   : {self.web3.from_wei(past_eth, 'ether'):.6f} ETH")

        try:
            past_cbbtc = self.contract.functions.balanceOf(self.wallet_address).call(
                block_identifier=self.target_block
            )
            print(f"cbBTC : {past_cbbtc / (10 ** self.CBTC_DECIMALS):.8f} cbBTC")
        except Exception as e:
            print(f"❌ Error fetching past cbBTC: {e}")
            print("   → Common fix: try smaller 'days_ago' (Alchemy free tier has archive limits)")


# ================== RUN (exact same UX as original) ==================
if __name__ == "__main__":
    wallet_address = input("Enter your Base wallet address: ").strip()
    days_ago = int(input("How many days ago? "))
    api_key = input("Enter your Alchemy API key: ").strip()

    tracker = WalletTracker(wallet_address, days_ago, api_key)
    tracker.track()
