import logging
import time
import pytz
from datetime import datetime, timezone

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
        self.sclient = APIStreamClient(ssId=self.ssid, address=address, port=streaming_port)
    

    def get_account(self):
        resp = self.client.commandExecute('getMarginLevel')

        if not resp["status"]:
            raise Exception(f"Error retrieving margin level from xtb: {resp}")

        return resp["returnData"]

    
    def get_initial_candles(self, instrument, from_date, granularity='M1'):
        instrument = xtb_get_instrument(instrument)
        now = datetime.now(timezone.utc)
        candles = self.get_candles(instrument, from_date, now, granularity)

        return candles
    

    def get_candles(self, instrument, from_date, to_date, granularity='M1'):
        instrument = xtb_get_instrument(instrument)

        resp = self.client.commandExecute('getChartRangeRequest', {"info": {
            "start": time.mktime(from_date.timetuple()) * 1000,
            "end": time.mktime(to_date.timetuple()) * 1000,
            "period": period_to_mins[granularity],
            "symbol": instrument,
        }})

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
        pass
    

    def get_position_for_instrument(self, instrument):
        pass


    def new_stop_order(self, instrument, units, entry, stop, profit1, profit2):
        pass
