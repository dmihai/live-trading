from datetime import timedelta
from utils.time import get_current_time

import pandas as pd


class Strategy:
    def __init__(self, profit1_keep_ratio, move_stop_to_breakeven, pip_value, signal_expiry, skip_minutes):
        self._profit1_keep_ratio = profit1_keep_ratio
        self._move_stop_to_breakeven = move_stop_to_breakeven
        self._pip_value = pip_value
        self._signal_expiry = signal_expiry
        self._skip_minutes = skip_minutes

        self._data = pd.DataFrame()
        self._orders = []
        self._skip_until = get_current_time()
    

    def load_data(self, data: pd.DataFrame):
        self._data = data.copy()
    

    def trade(self):
        pass
    

    def _is_trade_valid(self):
        now = get_current_time()

        if now > self._skip_until:
            return True
        
        return False
    

    def _new_order(self, order):
        now = get_current_time()
        self._skip_until = now + timedelta(minutes=self._skip_minutes)

        self._orders.append(order)
