from walletBalance import Wallet
from marketRate import CryptoRatioFetcher
from panPrice import PanPrice


class Swap:
    def __init__(self):
        self.wallet = Wallet()
        self.fetcher = CryptoRatioFetcher()
        self.pan = PanPrice()
        
        self.cbbtc_balance = 0.0
        self.eth_balance = 0.0
        self.market_ratio = 0.0       # CoinGecko BTC/ETH (for reference & value calc)
        #self.internal_ratio = 0.0     # Current pool price (for swap estimate)
        self.preferred_ratio = 0.0    # ← NOW comes from run_interactive() liquidity range


    def fetch_all_data(self):
        print("=" * 70)
        print("🔄 CBTC-ETH REBALANCER - LIQUIDITY RANGE MODE")
        print("=" * 70)

        # 1. Wallet balances
        print("\n1️⃣  Updating wallet balances...")
        
        if (self.wallet.update_balances() == False):
            return

        self.eth_balance = float(self.wallet.eth_balance)
        self.cbbtc_balance = float(self.wallet.cbbtc_balance)

        if self.cbbtc_balance <= 0:
            self.cbbtc_balance = 0.00000001
            #print("⚠️  No cbBTC found – nothing to rebalance.")
            #return False

        if self.eth_balance <= 0:
            self.eth_balance = 0.00000001

        # 2. Market prices (reference only)
        print("\n2️⃣  Fetching CoinGecko prices...")
        self.market_ratio = self.fetcher.get_btc_eth_ratio()

        # 3. Preferred ratio = ETH needed per 1 cbBTC for your chosen range
        print("\n3️⃣  Setting preferred ratio from your liquidity range...")
        print("     (This calls pan.run_interactive() → enter lower/upper %)")
        
        self.preferred_ratio = self.pan.run_interactive()
        
        if self.preferred_ratio is None or self.preferred_ratio <= 0:
            print("❌ failed to get preferred ratio")
            return False

        #self.internal_ratio = self.pan.current_price   # live pool price for swap suggestion

        # Summary
        current_holdings_ratio = self.eth_balance / self.cbbtc_balance
        print(f"\n✅ ALL DATA READY")
        print(f"   Current holdings ratio : {current_holdings_ratio:.6f} ETH per cbBTC")
        print(f"   Market ratio           : {self.market_ratio:.4f}")
        print(f"   Preferred ratio (range): {self.preferred_ratio:.6f} ← USING THIS")
        #print(f"   Current pool price     : {self.internal_ratio:.6f}")
        
        return True


    def calculate_targets(self):
        """Exact same spreadsheet math as your original file"""
        if self.cbbtc_balance <= 0 or self.preferred_ratio <= 0:
            print("❌ run fetch_all_data() first")
            return None

        total_eth_equiv = self.eth_balance + (self.cbbtc_balance * self.market_ratio)

        denom = self.preferred_ratio + self.market_ratio
        target_btc = total_eth_equiv / denom
        target_eth = self.preferred_ratio * target_btc

        btc_delta = target_btc - self.cbbtc_balance
        eth_delta = target_eth - self.eth_balance

        print("\n" + "=" * 70)
        print("📊 REBALANCING RESULT")
        print("=" * 70)
        print(f"eth equivalent          : {total_eth_equiv:.6f}")
        print(f"target btc amount       : {target_btc:.8f}")
        print(f"target eth amount       : {target_eth:.6f}")

        print(f"\ncurrent ratio           : {self.eth_balance / self.cbbtc_balance:.6f}")
        print(f"market ratio            : {self.market_ratio:.4f}")
        print(f"preferred ratio (range) : {self.preferred_ratio:.6f}")

        # Match screenshot style exactly
        if btc_delta < 0:
            print(f"btc delta               : ({-btc_delta:.8f})")
        else:
            print(f"btc delta               : {btc_delta:.8f}")
        print(f"eth delta               : {eth_delta:+.6f}")

        return {
            'total_eth_equiv': total_eth_equiv,
            'target_btc': target_btc,
            'target_eth': target_eth,
            'btc_delta': btc_delta,
            'eth_delta': eth_delta
        }


    def run(self):
        print("🧮 Swap Amount Calculator (cbBTC ↔ ETH rebalancer)")
        print("   Preferred ratio = ETH needed per 1 cbBTC for your chosen liquidity range\n")

        if self.fetch_all_data():
            self.calculate_targets()
            print("\n" + "=" * 70)


if __name__ == "__main__":
    swapper = Swap()
    swapper.run()
