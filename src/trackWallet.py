from web3 import Web3

# ================== INPUTS ==================
wallet_address = input("Enter your Base wallet address: ").strip()
days_ago = int(input("How many days ago? "))
api_key = input("Enter your Alchemy API key: ").strip()

# ================== SETUP ==================
RPC_URL = f"https://base-mainnet.g.alchemy.com/v2/{api_key}"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("❌ Failed to connect to Base network")
    exit()

wallet_address = web3.to_checksum_address(wallet_address)

# Correct cbBTC contract on Base
CBTC_ADDRESS = web3.to_checksum_address("0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf")

# Minimal ABI (just balanceOf)
CBTC_ABI = [{
    "constant": True,
    "inputs": [{"name": "who", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "", "type": "uint256"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function"
}]

contract = web3.eth.contract(address=CBTC_ADDRESS, abi=CBTC_ABI)
CBTC_DECIMALS = 8  # cbBTC uses 8 decimals (like BTC)

# Better block estimate for Base (~2s block time)
blocks_per_day = 43200
current_block = web3.eth.block_number
target_block = max(1, current_block - (days_ago * blocks_per_day))

print(f"\n📍 Current block : {current_block:,}")
print(f"📍 Target block (~{days_ago} days ago): {target_block:,}\n")

# ================== CURRENT BALANCES ==================
print("🔄 Fetching CURRENT balances...\n")

current_eth = web3.eth.get_balance(wallet_address)
print(f"ETH   : {web3.from_wei(current_eth, 'ether'):.6f} ETH")

try:
    current_cbbtc = contract.functions.balanceOf(wallet_address).call()
    print(f"cbBTC : {current_cbbtc / (10 ** CBTC_DECIMALS):.8f} cbBTC")
except Exception as e:
    print(f"❌ Error fetching current cbBTC: {e}")

# ================== PAST BALANCES ==================
print(f"\n🔄 Fetching balances ~{days_ago} day(s) ago (block {target_block})...\n")

past_eth = web3.eth.get_balance(wallet_address, block_identifier=target_block)
print(f"ETH   : {web3.from_wei(past_eth, 'ether'):.6f} ETH")

try:
    past_cbbtc = contract.functions.balanceOf(wallet_address).call(block_identifier=target_block)
    print(f"cbBTC : {past_cbbtc / (10 ** CBTC_DECIMALS):.8f} cbBTC")
except Exception as e:
    print(f"❌ Error fetching past cbBTC: {e}")
    print("   → Common fix: try smaller 'days_ago' (Alchemy free tier has archive limits)")
