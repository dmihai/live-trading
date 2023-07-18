import logging
import time
import pytz
from datetime import datetime, timezone, timedelta

from providers.xtbAPIConnector import APIClient, APIStreamClient, loginCommand
from constants import period_to_mins


def xtb_get_instrument(instrument):
    return instrument.replace("_", "")


class XTB():
    def __init__(self, user_id, password, address='xapi.xtb.com', port=5124, streaming_port=5125):
        self.client = APIClient(address=address, port=port)
        loginResponse = self.client.execute(loginCommand(userId=user_id, password=password))

        if(loginResponse['status'] == False):
            logging.error('Login failed. Error code: {0}'.format(loginResponse['errorCode']))
            return

        self.ssid = loginResponse['streamSessionId']
        # self.sclient = APIStreamClient(ssId=self.ssid, address=address, port=streaming_port)
    

    def get_account(self):
        resp = self.client.commandExecute('getMarginLevel')

        if not resp["status"]:
            raise Exception(f"Error retrieving margin level from xtb: {resp}")

        return resp["returnData"]

    
    def get_initial_candles(self, instrument, from_date, granularity='M1'):
        now = datetime.now(timezone.utc)
        candles = self.get_candles(instrument, from_date, now, granularity)

        return candles
    

    def get_candles(self, instrument, from_date, to_date, granularity='M1'):
        params = {
            "start": time.mktime(from_date.timetuple()) * 1000,
            "period": period_to_mins[granularity],
            "symbol": xtb_get_instrument(instrument),
        }

        command = "getChartLastRequest"
        if to_date is not None:
            params['end'] = time.mktime(to_date.timetuple()) * 1000
            command = "getChartRangeRequest"
        
        resp = self.client.commandExecute(command, {"info": params})

        if not resp["status"]:
            raise Exception(f"Error retrieving candles from xtb: {resp}")

        factor = pow(10, resp["returnData"]["digits"])

        return [
            {
                'open_price': float(candle['open'] / factor),
                'high_price': float((candle['open'] + candle['high']) / factor),
                'low_price': float((candle['open'] + candle['low']) / factor),
                'close_price': float((candle['open'] + candle['close']) / factor),
                'volume': candle['vol'],
                'timestamp': datetime.fromtimestamp(candle['ctm'] / 1000, tz=pytz.timezone('CET')),
            }
            for candle in resp["returnData"]["rateInfos"]
        ]


    def get_ask_price(self, instrument):
        resp = self.client.commandExecute('getSymbol', {
            "symbol": xtb_get_instrument(instrument),
        })

        if not resp["status"]:
            raise Exception(f"Error retrieving symbol from xtb: {resp}")

        return resp["returnData"]["ask"]
    

    def get_position_for_instrument(self, instrument):
        resp = self.client.commandExecute('getTrades', {
            "openedOnly": True,
        })

        if not resp["status"]:
            raise Exception(f"Error retrieving trades from xtb: {resp}")
        
        position = {
            'short': 0,
            'long': 0,
        }

        for trade in resp["returnData"]:
            if trade["symbol"] == xtb_get_instrument(instrument):
                pos = trade["position"]
                if pos > 0:
                    position["long"] += pos
                else:
                    position["short"] += abs(pos)

        return position


    def new_stop_order(self, instrument, units, entry, stop, profit1, profit2):
        units1 = round(units / 2)
        units2 = units - units1

        type = 4  # BUY_STOP
        if entry > profit1:
            type = 5  # SELL_STOP

        order1 = self._create_order(type, instrument, units1, entry, stop, profit1)
        order2 = self._create_order(type, instrument, units2, entry, stop, profit2)

        return (order1, order2)
    

    def _create_order(self, type, instrument, units, entry, stop, profit):
        now = datetime.now(timezone.utc)
        expiration = now + timedelta(days=30)  # expiration hard coded to 30 days

        resp = self.client.commandExecute('tradeTransaction', {"tradeTransInfo": {
            "cmd": type,
            "expiration": time.mktime(expiration.timetuple()) * 1000,
            "offset": 0,
            "order": 0,
            "price": entry,
            "sl": stop,
            "symbol": xtb_get_instrument(instrument),
            "tp": profit,
            "type": 0,  # OPEN
            "volume": units,
        }})

        if not resp["status"]:
            raise Exception(f"Error creating order on xtb: {resp}")

        return resp["returnData"]
