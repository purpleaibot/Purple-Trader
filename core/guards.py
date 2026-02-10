import ccxt
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorrelationGuard:
    """
    Prevents over-exposure to a single base or quote currency.
    Example: Limits max 2 active trades with 'BTC' as base.
    """
    def __init__(self, max_trades_per_asset: int = 2):
        self.max_trades_per_asset = max_trades_per_asset
        # Tracks active positions: {'BTC': 1, 'ETH': 2, ...}
        self.active_positions: Dict[str, int] = {}

    def update_positions(self, open_positions: List[str]):
        """
        Updates internal tracking based on a list of currently open symbols.
        Assumes symbols are in 'BASE/QUOTE' format (e.g., 'BTC/USDT').
        """
        self.active_positions = {}
        for symbol in open_positions:
            base, quote = symbol.split('/')
            self.active_positions[base] = self.active_positions.get(base, 0) + 1
            # We typically care more about base exposure, but could track quote too if needed.

    def check(self, symbol: str) -> bool:
        """
        Checks if a new trade for 'symbol' (e.g., 'SOL/USDT') is allowed.
        Returns True if allowed, False if limit reached.
        """
        base, quote = symbol.split('/')
        current_count = self.active_positions.get(base, 0)
        
        if current_count >= self.max_trades_per_asset:
            logger.warning(f"Correlation Guard Block: Max trades reached for {base} ({current_count}/{self.max_trades_per_asset})")
            return False
        
        return True

class LiquidityGuard:
    """
    Ensures sufficient liquidity and tight spread before trading.
    """
    def __init__(self, exchange: ccxt.Exchange, max_spread_pct: float = 0.005, min_depth_usdt: float = 1000.0):
        self.exchange = exchange
        self.max_spread_pct = max_spread_pct
        self.min_depth_usdt = min_depth_usdt

    def check(self, symbol: str) -> bool:
        """
        Fetches order book and validates spread and depth.
        Returns True if safe to trade, False otherwise.
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol)
            if not order_book['bids'] or not order_book['asks']:
                logger.warning(f"Liquidity Guard Block: Empty order book for {symbol}")
                return False

            best_bid = order_book['bids'][0][0]
            best_ask = order_book['asks'][0][0]
            
            # 1. Spread Check
            spread = (best_ask - best_bid) / best_bid
            if spread > self.max_spread_pct:
                logger.warning(f"Liquidity Guard Block: Spread too high for {symbol} ({spread:.2%})")
                return False

            # 2. Depth Check (Simple approximate: bid depth)
            # Sum volume of top 5 bids * price
            bid_depth = sum([bid[0] * bid[1] for bid in order_book['bids'][:5]])
            if bid_depth < self.min_depth_usdt:
                logger.warning(f"Liquidity Guard Block: Insufficient depth for {symbol} (${bid_depth:.2f} < ${self.min_depth_usdt})")
                return False

            return True

        except Exception as e:
            logger.error(f"Liquidity Guard Error checking {symbol}: {e}")
            return False
