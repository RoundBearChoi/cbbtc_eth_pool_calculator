from web3 import Web3
import sys
from datetime import datetime, timezone, timedelta


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

    def _format_kst(self, timestamp: int) -> str:
        """Convert Unix timestamp to KST string (UTC+9)."""
        try:
            utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            kst_dt = utc_dt + timedelta(hours=9)
            return kst_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "N/A"

    def track(self):
        """Run the full balance tracking with clean KST timestamps."""
        # Fetch block timestamps once
        try:
            current_ts = self.web3.eth.get_block(self.current_block)['timestamp']
            current_kst = self._format_kst(current_ts)
        except Exception:
            current_kst = "N/A"

        try:
            target_ts = self.web3.eth.get_block(self.target_block)['timestamp']
            target_kst = self._format_kst(target_ts)
        except Exception:
            target_kst = "N/A"

        print('')
        print(f"📍 Current block : {self.current_block:,} ({current_kst} KST)")
        print(f"📍 Target block  : {self.target_block:,} ({target_kst} KST)\n")

        # ================== CURRENT BALANCES ==================
        print(f"🔄 Fetching CURRENT balances ({current_kst} KST)...")

        current_eth = self.web3.eth.get_balance(self.wallet_address)
        print(f"ETH   : {self.web3.from_wei(current_eth, 'ether'):.6f} ETH")

        try:
            current_cbbtc = self.contract.functions.balanceOf(self.wallet_address).call()
            print(f"cbBTC : {current_cbbtc / (10 ** self.CBTC_DECIMALS):.8f} cbBTC")
        except Exception as e:
            print(f"❌ Error fetching current cbBTC: {e}")

        # ================== PAST BALANCES ==================
        print(f"\n🔄 Fetching balances ~{self.days_ago} day(s) ago ({target_kst} KST)...")

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


# ================== RUN (CLI + interactive fallback) ==================
if __name__ == "__main__":
    # Support: python trackWallet.py WALLET_ADDRESS API_KEY
    # If any is left blank or missing → asks interactively
    if len(sys.argv) > 1 and sys.argv[1].strip():
        wallet_address = sys.argv[1].strip()
    else:
        wallet_address = input("Enter your Base wallet address: ").strip()

    if len(sys.argv) > 2 and sys.argv[2].strip():
        api_key = sys.argv[2].strip()
    else:
        api_key = input("Enter your Alchemy API key: ").strip()

    days_ago = int(input("How many days ago? "))

    tracker = WalletTracker(wallet_address, days_ago, api_key)
    tracker.track()
