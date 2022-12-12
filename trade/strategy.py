from datetime import timedelta
import pandas as pd
import logging

from utils.time import get_current_time
from providers.oanda import Oanda
from constants import pip_values


class Strategy:
    def __init__(self, instrument, api: Oanda):
        self._instrument = instrument
        self._api = api

        self._risk_per_trade = 0.01
        self._profit1_keep_ratio = 0.5
        self._move_stop_to_breakeven = False
        self._signal_expiry = 100
        self._skip_minutes = 240

        if instrument in pip_values:
            self._pip_value = pip_values[instrument]
        else:
            logging.warning(f"Instrument {instrument} not found in constants.py, pip_value defaults to 0.0001")
            self._pip_value = 0.0001

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

        units = self.__get_position_size(order['entry'], order['stop'])
        self._api.new_stop_order(self._instrument, units, order['entry'], order['stop'], order['profit1'], order['profit2'])

        self._orders.append(order)
    

    def __get_position_size(self, entry, stop):
        stop_loss = entry - stop

        account = self._api.get_account()
        account_balance = float(account['balance'])
        account_currency = account['currency'].upper()

        base_currency = self._instrument[0:3].upper()
        counter_currency = self._instrument[4:7].upper()

        risk_conversion = 1
        if base_currency == account_currency:
            risk_conversion = entry
        elif counter_currency == account_currency:
            risk_conversion = 1
        else:
            pair1 = f"{counter_currency}_{account_currency}"
            pair2 = f"{account_currency}_{counter_currency}"
            if pair1 in pip_values:
                risk_conversion = 1 / self._api.get_ask_price(pair1)
            elif pair2 in pip_values:
                risk_conversion = self._api.get_ask_price(pair2)

        stop_loss_pips = stop_loss / self._pip_value
        risk_value = account_balance * self._risk_per_trade * risk_conversion

        risk_value_per_pip = risk_value / stop_loss_pips

        return round(risk_value_per_pip / self._pip_value)
