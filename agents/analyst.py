import os
import requests
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables (for API keys)
load_dotenv()

logger = logging.getLogger(__name__)

class CryptoAnalyst:
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        # In a real implementation, we'd use a specific LLM library.
        # Here we define the interface for sentiment analysis.
        self.sentiment_prompt = """
        Analyze the following news snippets for {symbol} and determine the overall market sentiment.
        
        Snippets:
        {snippets}
        
        Respond ONLY with a JSON object in this format:
        {{
            "verdict": "BULLISH" | "BEARISH" | "NEUTRAL",
            "score": float (0.0 to 1.0),
            "reason": "short explanation"
        }}
        """

    def fetch_news(self, symbol: str) -> List[str]:
        """Fetch latest crypto news for a symbol using Brave Search API."""
        if not self.brave_api_key:
            logger.error("BRAVE_API_KEY not found in environment.")
            return []

        query = f"{symbol} crypto news"
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        params = {"q": query, "count": 5}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            snippets = []
            if "web" in data and "results" in data["web"]:
                for result in data["web"]["results"]:
                    snippets.append(result.get("description", ""))
            
            return snippets
        except Exception as e:
            logger.error(f"Error fetching news from Brave: {e}")
            return []

    def analyze_sentiment(self, symbol: str, snippets: List[str] = None) -> Dict:
        """
        Analyze sentiment for a symbol. 
        If snippets are provided, uses them. Otherwise fetches new ones.
        """
        if snippets is None:
            snippets = self.fetch_news(symbol)

        if not snippets:
            return {
                "verdict": "NEUTRAL",
                "score": 0.5,
                "reason": "No recent news found for analysis."
            }

        # Combine snippets for the prompt
        snippets_text = "\n---\n".join(snippets)
        
        # NOTE: In the current OpenClaw setup, the main agent (ME) will handle 
        # the LLM call using the 'oracle' or direct reasoning.
        # This function provides the structured input for that call.
        
        # For the purpose of Story 3.1, we return a "to-be-filled" structure
        # or we could implement a mock call to demonstrate.
        
        # Let's assume for this implementation we use a placeholder or 
        # simple keyword-based logic if no LLM is configured.
        
        # MOCK IMPLEMENTATION (Story 3.1 focus is the structure/sandbox)
        # In a production environment, this would hit OpenAI/Gemini API.
        
        bullish_keywords = ["bullish", "pump", "surge", "gain", "breakout", "accumulating", "buy"]
        bearish_keywords = ["bearish", "dump", "drop", "loss", "crash", "selling", "sell"]
        
        full_text = snippets_text.lower()
        bull_count = sum(1 for k in bullish_keywords if k in full_text)
        bear_count = sum(1 for k in bearish_keywords if k in full_text)
        
        if bull_count > bear_count:
            return {
                "verdict": "BULLISH",
                "score": 0.5 + (bull_count / (bull_count + bear_count + 1) * 0.5),
                "reason": f"Detected {bull_count} bullish signals in recent news."
            }
        elif bear_count > bull_count:
            return {
                "verdict": "BEARISH",
                "score": 0.5 - (bear_count / (bull_count + bear_count + 1) * 0.5),
                "reason": f"Detected {bear_count} bearish signals in recent news."
            }
        else:
            return {
                "verdict": "NEUTRAL",
                "score": 0.5,
                "reason": "News sentiment is mixed or inconclusive."
            }

if __name__ == "__main__":
    # Test run
    analyst = CryptoAnalyst()
    symbol = "BTC"
    print(f"Analyzing sentiment for {symbol}...")
    result = analyst.analyze_sentiment(symbol)
    print(json.dumps(result, indent=4))
