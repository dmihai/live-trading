class Strategy:
    def __init__(self, data, profit1_keep_ratio, move_stop_to_breakeven, pip_value, signal_expiry):
        self._profit1_keep_ratio = profit1_keep_ratio
        self._move_stop_to_breakeven = move_stop_to_breakeven
        self._pip_value = pip_value
        self._signal_expiry = signal_expiry

        self._data = data.copy()
