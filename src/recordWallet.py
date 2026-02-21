import csv
import os
from datetime import datetime

from walletBalance import Wallet
from geckoPrices import Prices


class Recorder:
    def __init__(self, csv_file="base-btc-eth.csv"):
        self.wallet = Wallet()
        self.prices = Prices()
        self.csv_file = csv_file
        self._ensure_csv_exists()

    
    def _ensure_csv_exists(self):
        """Create the CSV file with correct headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'date', 'time', 'btc_price', 'eth_price', 'btc_eth_ratio',
                    'cbbtc_balance', 'eth_balance', 'wallet_ratio',
                    'btc_equivalent', 'total_usd_value'
                ])
            print(f"✅ Created new CSV file: {self.csv_file}")


    def record(self):
        """Record current wallet balances + CoinGecko prices and append to CSV"""
        self.wallet.update_balances()

        if self.wallet.address is None:
            print('')
            print("❌ could not load wallet - recording cancelled")
            return

        print('')
        print('🔄 fetching btc, eth prices from coingecko...')
        btc_price = self.prices.getPrice('btc')
        eth_price = self.prices.getPrice('eth')

        if btc_price is None or eth_price is None:
            print("❌ could not fetch prices - recording cancelled")
            return

        # Convert both to float for safe calculations
        cbbtc = float(self.wallet.cbbtc_balance)
        eth    = float(self.wallet.eth_balance)

        # === Calculations (exactly like your sample CSV) ===
        btc_eth_ratio = btc_price / eth_price
        wallet_ratio  = eth / cbbtc if cbbtc > 0 else 0.0
        btc_equivalent = cbbtc + (eth / btc_eth_ratio)
        total_usd_value = btc_equivalent * btc_price

        # Timestamp
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        # Row (same precision as your CSV)
        row = [
            date_str,
            time_str,
            round(btc_price, 2),
            round(eth_price, 2),
            round(btc_eth_ratio, 6),
            round(cbbtc, 8),
            round(eth, 8),
            round(wallet_ratio, 8),
            round(btc_equivalent, 8),
            round(total_usd_value, 2)
        ]

        # Append to CSV
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print('')
        print(f"✅ recorded successfully at {date_str} {time_str}")
        print(f"   BTC   : ${btc_price:,.2f}")
        print(f"   ETH   : ${eth_price:,.2f}")
        print(f"   Wallet: {cbbtc:.8f} cbBTC + {eth:.6f} ETH")
        print(f"   Ratio : {wallet_ratio:.2f} ETH per cbBTC")
        print(f"   BTC eq: {btc_equivalent:.8f} BTC")
        print(f"   Value : ${total_usd_value:,.2f}")


if __name__ == "__main__":
    recorder = Recorder()
    recorder.record()
