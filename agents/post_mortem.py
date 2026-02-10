import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from core.database import SessionLocal, Trade

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostMortemAgent:
    """
    Analyzes past trades and generates a 'Lessons Learned' report.
    """
    def __init__(self, report_dir: str = "data/reports"):
        self.report_dir = report_dir
        os.makedirs(self.report_dir, exist_ok=True)

    def analyze_trades(self, start_date: datetime = None, end_date: datetime = None) -> str:
        """
        Analyzes trades within a date range and generates a report.
        
        Args:
            start_date: Beginning of analysis period (default: 7 days ago)
            end_date: End of analysis period (default: now)
        
        Returns:
            str: Path to the generated report file
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.utcnow()

        logger.info(f"Analyzing trades from {start_date} to {end_date}")

        # 1. Query trades from database
        db = SessionLocal()
        try:
            trades = db.query(Trade).filter(
                Trade.entry_time >= start_date,
                Trade.entry_time <= end_date,
                Trade.status == "CLOSED"
            ).all()
        finally:
            db.close()

        if not trades:
            logger.warning("No closed trades found in the specified period.")
            return None

        # 2. Analyze trade data
        analysis = self._analyze_data(trades)

        # 3. Generate LLM insights (placeholder for now)
        llm_insights = self._generate_llm_insights(analysis)

        # 4. Create markdown report
        report_path = self._create_report(start_date, end_date, analysis, llm_insights)

        logger.info(f"Post-mortem report saved to {report_path}")
        return report_path

    def _analyze_data(self, trades: List[Trade]) -> Dict:
        """Performs statistical analysis on trades."""
        total_trades = len(trades)
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in trades)
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0

        # Group by symbol
        by_symbol = {}
        for t in trades:
            if t.symbol not in by_symbol:
                by_symbol[t.symbol] = {'wins': 0, 'losses': 0, 'total_pnl': 0}
            
            if t.pnl > 0:
                by_symbol[t.symbol]['wins'] += 1
            else:
                by_symbol[t.symbol]['losses'] += 1
            by_symbol[t.symbol]['total_pnl'] += t.pnl

        return {
            'total_trades': total_trades,
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'by_symbol': by_symbol
        }

    def _generate_llm_insights(self, analysis: Dict) -> str:
        """
        Generates insights using LLM (placeholder implementation).
        In production, this would call an LLM API with the analysis data.
        """
        # Placeholder logic - replace with actual LLM call
        insights = f"""
## AI-Generated Insights

Based on {analysis['total_trades']} trades analyzed:

**Performance Summary:**
- Win Rate: {analysis['win_rate']:.1f}%
- Total P&L: ${analysis['total_pnl']:.2f}

**Key Observations:**
1. {'Strong performance' if analysis['win_rate'] > 50 else 'Needs improvement'} in trade selection.
2. Review risk management if losses are clustering.
3. Consider reducing exposure on underperforming symbols.

**Recommended Actions:**
- {'Continue current strategy' if analysis['total_pnl'] > 0 else 'Reassess entry/exit logic'}
- Monitor correlation between trades
- Adjust position sizing based on recent performance
"""
        return insights

    def _create_report(self, start_date: datetime, end_date: datetime, 
                      analysis: Dict, llm_insights: str) -> str:
        """Creates and saves a markdown report."""
        report_filename = f"post_mortem_{start_date.strftime('%Y-%m-%d')}.md"
        report_path = os.path.join(self.report_dir, report_filename)

        report_content = f"""# Post-Mortem Trade Analysis
**Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}  
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

---

## Executive Summary

- **Total Trades:** {analysis['total_trades']}
- **Wins:** {analysis['wins']}
- **Losses:** {analysis['losses']}
- **Win Rate:** {analysis['win_rate']:.1f}%
- **Net P&L:** ${analysis['total_pnl']:.2f}

---

## Performance by Symbol

| Symbol | Wins | Losses | Total P&L |
|--------|------|--------|-----------|
"""
        for symbol, data in analysis['by_symbol'].items():
            report_content += f"| {symbol} | {data['wins']} | {data['losses']} | ${data['total_pnl']:.2f} |\n"

        report_content += f"\n---\n\n{llm_insights}\n"

        with open(report_path, 'w') as f:
            f.write(report_content)

        return report_path

if __name__ == "__main__":
    # Test run
    agent = PostMortemAgent()
    report = agent.analyze_trades()
    if report:
        print(f"Report generated: {report}")
    else:
        print("No trades to analyze")
