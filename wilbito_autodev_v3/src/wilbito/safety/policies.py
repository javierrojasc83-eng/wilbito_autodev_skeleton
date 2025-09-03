class PolicyGate:
    """Valida políticas de seguridad y gobernanza."""

    def __init__(self, trading_hours=(0, 23), max_lot=10):
        self.trading_hours = trading_hours
        self.max_lot = max_lot

    def check_trade(self, hour: int, lot: float) -> bool:
        if not (self.trading_hours[0] <= hour <= self.trading_hours[1]):
            return False
        if lot > self.max_lot:
            return False
        return True
