import ccxt
import os
from dotenv import load_dotenv

# PROJECT ID: live_pull_001
# Purpose: Real data pull for Alex to prove the Developer isn't sleeping.

def fetch_live_prices():
    try:
        # Initializing Binance exchange
        exchange = ccxt.binance({
            'enableRateLimit': True,
        })
        
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
        print(f"📡 Fetching live prices for: {', '.join(symbols)}...")
        
        tickers = exchange.fetch_tickers(symbols)
        
        results = []
        for symbol in symbols:
            price = tickers[symbol]['last']
            change = tickers[symbol]['percentage']
            results.append(f"• {symbol}: ${price:,.2f} ({'+' if change >= 0 else ''}{change:.2f}%)")
        
        return "\n".join(results)
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    print(fetch_live_prices())
