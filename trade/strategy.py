from datetime import timedelta
import pandas as pd

from utils.time import get_current_time
from providers.oanda import Oanda


class Strategy:
    def __init__(self, instrument, api: Oanda):
        self._instrument = instrument
        self._api = api

        params = {
            'profit1_keep_ratio': 0.5,
            'move_stop_to_breakeven': False,
            'pip_value': 0.0001,
            'signal_expiry': 100,
            'skip_minutes': 240
        }
        self.load_params(params)

        self._data = pd.DataFrame()
        self._orders = []
        self._skip_until = get_current_time()
    

    def load_params(self, params):
        for param, value in params.items():
            setattr(self, f"_{param}", value)
    

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
