import json
import logging
import os
from datetime import datetime

# Ensure logs directory exists
LOG_DIR = "core/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure dedicated signal logger
signal_logger = logging.getLogger("signal_logger")
signal_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "signals.log"))
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler.setFormatter(formatter)
signal_logger.addHandler(file_handler)

class SignalPackager:
    """
    Bundles trade data into a secure execution packet.
    """
    REQUIRED_FIELDS = ['symbol', 'side', 'entry_price', 'sl', 'tp', 'size', 'level', 'slevel']

    @staticmethod
    def package_trade(data: dict) -> dict:
        """
        Validates and packages trade data.
        
        Args:
            data (dict): Raw trade data containing:
                - symbol: str
                - side: str (BUY/SELL)
                - entry_price: float
                - sl: float
                - tp: float
                - size: float
                - level: int
                - slevel: int
                - (optional) strategy_verdict: str
                - (optional) agent_verdict: str
        
        Returns:
            dict: Secure JSON-serializable packet.
        
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # 1. Validate required fields
        missing = [f for f in SignalPackager.REQUIRED_FIELDS if f not in data]
        if missing:
            raise ValueError(f"Missing required fields for signal package: {missing}")

        # 2. Validate types (basic check)
        if not isinstance(data['symbol'], str) or '/' not in data['symbol']:
            raise ValueError(f"Invalid symbol format: {data['symbol']}")
        
        if data['side'] not in ['BUY', 'SELL']:
            raise ValueError(f"Invalid side: {data['side']}")
            
        if data['entry_price'] <= 0 or data['sl'] <= 0 or data['tp'] <= 0 or data['size'] <= 0:
            raise ValueError("Price, SL, TP, and Size must be positive.")

        # 3. Construct Packet
        packet = {
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0",
                "source": "Oracle-AI-Hub"
            },
            "trade": {
                "symbol": data['symbol'],
                "side": data['side'],
                "entry": float(data['entry_price']),
                "sl": float(data['sl']),
                "tp": float(data['tp']),
                "size": float(data['size']),
                "risk": {
                    "level": int(data['level']),
                    "slevel": int(data['slevel'])
                }
            },
            "context": {
                "strategy": data.get('strategy_verdict', 'N/A'),
                "sentiment": data.get('agent_verdict', 'N/A')
            }
        }
        
        # 4. Log Packet
        SignalPackager._log_packet(packet)
        
        return packet

    @staticmethod
    def _log_packet(packet: dict):
        """Logs the JSON packet to file."""
        try:
            log_entry = json.dumps(packet)
            signal_logger.info(log_entry)
        except Exception as e:
            # Fallback to standard logger if file logging fails
            logging.error(f"Failed to log signal packet: {e}")

if __name__ == "__main__":
    # Test run
    sample_data = {
        'symbol': 'BTC/USDT',
        'side': 'BUY',
        'entry_price': 50000.0,
        'sl': 49000.0,
        'tp': 53000.0,
        'size': 0.01,
        'level': 5,
        'slevel': 0,
        'strategy_verdict': 'BUY',
        'agent_verdict': 'BULLISH'
    }
    pkg = SignalPackager.package_trade(sample_data)
    print(json.dumps(pkg, indent=2))
