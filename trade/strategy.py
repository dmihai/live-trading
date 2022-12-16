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

        self._precision = self.__get_precision()
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
    

    def _calculate_order(self, entry, stop, profit1, profit2):
        return {
            'signal': 1 if entry > stop else -1,
            'entry': round(entry, self._precision),
            'stop': round(stop, self._precision),
            'profit1': round(profit1, self._precision),
            'profit2': round(profit2, self._precision)
        }


    def _new_order(self, order):
        now = get_current_time()

        try:
            position = self._api.get_position_for_instrument(self._instrument)
            if position['short'] == 0 and position['long'] == 0:
                units = self.__get_position_size(order['entry'], order['stop'])
                self._api.new_stop_order(self._instrument, units, order['entry'], order['stop'], order['profit1'], order['profit2'])
            else:
                logging.info(f"Order not created for instrument {self._instrument} because there are opened positions: {position}")
        except Exception as e:
            order_details = f"instrument: {self._instrument}, units: {units}, entry: {order['entry']}, stop: {order['stop']}, profit1: {order['profit1']}, profit2: {order['profit2']}"
            logging.warning(f"Failed to create new order for instrument {self._instrument}: {e} {order_details}")
        else:
            logging.info(f"Order successfully created for instrument {self._instrument}")
            self._skip_until = now + timedelta(minutes=self._skip_minutes)

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
    

    def __get_precision(self):
        n = self._pip_value
        precision = 0
        while n < 0.9:
            precision += 1
            n *= 10

        return precision + 1

