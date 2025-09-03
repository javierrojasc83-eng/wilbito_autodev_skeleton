def backtest(par: str = "XAUUSD", n: int = 100):
    """Backtest simulado."""
    # números dummy para demo
    win_rate = 50.0 + (n % 15)  # pseudo variable
    profit_factor = 1.3 + ((n % 10) / 20.0)
    result = {
        "par": par,
        "trades": n,
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
    }
    print(f"Trading → Backtest {par}: {result}")
    return result
