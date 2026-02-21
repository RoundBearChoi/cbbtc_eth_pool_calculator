import requests
from typing import Optional


class Prices:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()  # reuse connection for speed
        
        # Common ticker → CoinGecko ID mapping
        self.symbol_map = {
            'btc': 'bitcoin',
            'eth': 'ethereum',
            'sol': 'solana',
            'bnb': 'binancecoin',
            'xrp': 'ripple',
            'ada': 'cardano',
            'doge': 'dogecoin',
            'avax': 'avalanche-2',
            'link': 'chainlink',
            'dot': 'polkadot',
            'matic': 'matic-network',
            'ton': 'the-open-network',
            'shib': 'shiba-inu',
            'usdt': 'tether',
            'usdc': 'usd-coin',
        }


    def _get_coin_id(self, symbol: str) -> str:
        symbol = symbol.lower().strip()
        return self.symbol_map.get(symbol, symbol)


    def getPrice(self, symbol: str, vs_currency: str = 'usd') -> Optional[float]:
        """Returns raw float price (same as before)"""
        coin_id = self._get_coin_id(symbol)
        vs_currency = vs_currency.lower()

        url = f"{self.base_url}/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': vs_currency
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            price = data.get(coin_id, {}).get(vs_currency)
            return float(price) if price is not None else None

        except Exception as e:
            print('')
            print(f"❌ error getting price for {symbol}: {e}")
            return None


    def getPriceFormatted(self, symbol: str, vs_currency: str = 'usd') -> str:
        """
        Returns a beautiful string like "$67,820.45" or "1,234.56 EUR"
        """
        price = self.getPrice(symbol, vs_currency)
        if price is None:
            return "N/A"

        vs = vs_currency.lower()
        if vs == 'usd':
            return f"${price:,.2f}"
        elif vs == 'eur':
            return f"€{price:,.2f}"
        elif vs == 'krw':
            return f"₩{price:,.0f}"      # no decimals for won
        else:
            return f"{price:,.2f} {vs.upper()}"


if __name__ == "__main__":
    p = Prices()
    
    print("Current Prices (CoinGecko)")
    print(f"BTC   = {p.getPriceFormatted('btc')}")
    #print(p.getPrice('btc'))
