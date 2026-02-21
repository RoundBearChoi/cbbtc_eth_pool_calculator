import math
import requests
import sys


class PanPrice:
    POOL_ADDRESS = "0xC211e1f853A898Bd1302385CCdE55f33a8C4B3f3"
    

    def __init__(self):
        self.current_price = None  # WETH per 1 cbBTC
    

    def fetch_current_price(self) -> float:
        """Fetch live price from GeckoTerminal"""
        try:
            url = f"https://api.geckoterminal.com/api/v2/networks/base/pools/{self.POOL_ADDRESS}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()["data"]["attributes"]
            self.current_price = float(data["base_token_price_quote_token"])
            print('')
            print(f"✅ Fetched live price: {self.current_price:.6f} WETH = 1 cbBTC")
            return self.current_price
        except Exception as e:
            print(f"⚠️  Could not fetch live price: {e}")
            return None
    

    def set_current_price(self, price: float):
        """Manually set current price"""
        self.current_price = float(price)
        print(f"✅ Using manual price: {self.current_price:.6f} WETH = 1 cbBTC")
    

    @staticmethod
    def _calculate_weth_needed(p_current: float, lower_pct: float, upper_pct: float, amount_cbbtc: float = 1.0) -> float:
        """Core V3 liquidity math"""
        p_lower = p_current * (1 - lower_pct / 100)
        p_upper = p_current * (1 + upper_pct / 100)
        
        if p_lower >= p_current or p_upper <= p_current:
            raise ValueError("Current price must be strictly between lower and upper range")
        
        sqrt_p_lower = math.sqrt(p_lower)
        sqrt_p_current = math.sqrt(p_current)
        sqrt_p_upper = math.sqrt(p_upper)
        
        L = amount_cbbtc / (1 / sqrt_p_current - 1 / sqrt_p_upper)
        weth_needed = L * (sqrt_p_current - sqrt_p_lower)
        
        return weth_needed
    

    def get_eth_needed(self, lower_pct: float, upper_pct: float, amount_cbbtc: float = 1.0) -> float:
        """
        Returns ONLY the exact WETH amount needed.
        No prints, no dict — just the float you asked for.
        """
        if self.current_price is None:
            raise ValueError("Call fetch_current_price() or set_current_price() first!")
        
        return self._calculate_weth_needed(self.current_price, lower_pct, upper_pct, amount_cbbtc)
   

    def run_interactive(self) -> float:
        # Try live price first
        self.fetch_current_price()
        
        # Fallback to manual input
        if self.current_price is None:
            try:
                manual_price = float(input("Enter current WETH per 1 cbBTC (from PancakeSwap UI): "))
                self.set_current_price(manual_price)
            except ValueError:
                print("❌ Invalid input. Exiting.")
                sys.exit(1)
        
        print("\nEnter percentages for the range (positive numbers only)")
        print("Example: lower = 5 → -5%, upper = 5 → +5%")
        
        try:
            lower_pct = float(input("\nLower range % (e.g. 3): "))
            upper_pct = float(input("Upper range % (e.g. 4): "))
            
            if lower_pct <= 0 or upper_pct <= 0:
                print("Percentages must be positive.")
                sys.exit(1)
                
            eth_needed = self.get_eth_needed(lower_pct, upper_pct)
            print('')
            print(f"internal ratio 1 cbbtc : {eth_needed:.6f} weth")
            return eth_needed    

        except ValueError:
            print("Please enter valid numbers.")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

        return 0.0


if __name__ == "__main__":
    pan = PanPrice()
    ratio = pan.run_interactive()
    #print(ratio)
