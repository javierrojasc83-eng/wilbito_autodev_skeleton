from typing import Dict, Any
import random
from rich import print

class TradingAgent:
    def backtest(self, par: str = "XAUUSD", n: int = 100) -> Dict[str, Any]:
        # Mock simple
        results = {
            "par": par,
            "trades": n,
            "win_rate": round(40 + random.random()*20, 2),
            "profit_factor": round(0.9 + random.random()*1.2, 2),
        }
        print(f"[magenta]Trading[/magenta] → Backtest {par}: {results}")
        return results
