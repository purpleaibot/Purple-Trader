import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel:
    """Defines parameters for each risk level."""
    def __init__(self, level: int, max_position_pct: float, max_daily_loss_pct: float, description: str):
        self.level = level
        self.max_position_pct = max_position_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.description = description

class RiskEngine:
    """
    Manages risk exposure using a 10-level system.
    
    Levels 1-3: Conservative (Low exposure, tight stops)
    Levels 4-7: Moderate (Balanced growth)
    Levels 8-10: Aggressive (High exposure, wider stops)
    """
    
    def __init__(self, initial_level: int = 1):
        self.current_level = initial_level
        self.levels = self._define_risk_levels()
        logger.info(f"Risk Engine initialized at Level {self.current_level}")

    def _define_risk_levels(self) -> dict:
        """Defines the 10 risk levels with increasing exposure."""
        return {
            1: RiskLevel(1, 0.01, 0.005, "Extreme Caution"),
            2: RiskLevel(2, 0.02, 0.010, "Very Conservative"),
            3: RiskLevel(3, 0.03, 0.015, "Conservative"),
            4: RiskLevel(4, 0.05, 0.020, "Moderate-Low"),
            5: RiskLevel(5, 0.07, 0.025, "Moderate"),
            6: RiskLevel(6, 0.10, 0.030, "Moderate-High"),
            7: RiskLevel(7, 0.12, 0.035, "Growth"),
            8: RiskLevel(8, 0.15, 0.040, "Aggressive"),
            9: RiskLevel(9, 0.18, 0.045, "Very Aggressive"),
            10: RiskLevel(10, 0.20, 0.050, "Max Risk")
        }

    def set_risk_level(self, level: int):
        """Manually sets the risk level."""
        if level not in self.levels:
            raise ValueError(f"Invalid risk level: {level}. Must be between 1 and 10.")
        self.current_level = level
        logger.info(f"Risk level set to {self.current_level}: {self.levels[level].description}")

    def get_current_params(self) -> RiskLevel:
        """Returns the parameters for the current risk level."""
        return self.levels[self.current_level]

    def calculate_position_size(self, account_balance: float) -> float:
        """Calculates the maximum position size based on current risk level."""
        params = self.get_current_params()
        return account_balance * params.max_position_pct

    def check_daily_loss(self, current_daily_loss: float, account_balance: float) -> bool:
        """
        Checks if the daily loss limit has been breached.
        Returns True if trading should STOP, False otherwise.
        """
        params = self.get_current_params()
        max_loss = account_balance * params.max_daily_loss_pct
        
        if current_daily_loss >= max_loss:
            logger.warning(f"Daily loss limit reached! Level {self.current_level} limit: {max_loss:.2f}")
            return True
        return False

    def dynamic_adjustment(self, drawdown_pct: float):
        """
        Adjusts risk level based on drawdown percentage.
        If drawdown exceeds thresholds, risk level is reduced.
        """
        # Simple logic: Reduce level by 1 for every 5% drawdown
        # This is a placeholder for more complex logic
        if drawdown_pct > 0.05:
            new_level = max(1, self.current_level - 1)
            if new_level != self.current_level:
                logger.info(f"Drawdown detected ({drawdown_pct:.1%}). Reducing risk level to {new_level}")
                self.set_risk_level(new_level)
        elif drawdown_pct < 0.01 and self.current_level < 10:
             # Logic for increasing risk could go here (e.g., after profitable streak)
             pass

if __name__ == "__main__":
    # Simple test
    engine = RiskEngine(initial_level=5)
    print(f"Current Level: {engine.current_level}")
    print(f"Max Position (Balance 10000): {engine.calculate_position_size(10000)}")
    
    engine.set_risk_level(8)
    print(f"New Level: {engine.current_level}")
    print(f"Max Position (Balance 10000): {engine.calculate_position_size(10000)}")
