from datetime import timedelta
import pandas as pd

from utils.time import get_current_time
from providers.oanda import Oanda


class Strategy:
    def __init__(self, instrument, api: Oanda, profit1_keep_ratio, move_stop_to_breakeven, pip_value, signal_expiry, skip_minutes):
        self._instrument = instrument
        self._api = api
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

        # TODO: compute units to match risk
        units = 10000 if order['entry'] < order['profit1'] else -10000

        self._api.new_stop_order(self._instrument, units, order['entry'], order['stop'], order['profit1'], order['profit2'])

        self._orders.append(order)
