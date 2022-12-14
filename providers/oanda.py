from datetime import datetime, timezone, timedelta
import dateutil.parser
import logging

from providers.provider import Provider
from utils.time import date_to_rfc3339


class Oanda(Provider):
    def __init__(self, api_key, account_id, url='https://api-fxpractice.oanda.com'):
        super().__init__(url)

        self.account_id = account_id
        self.sess.headers.update({'Authorization': f"Bearer {api_key}"})
        self.sess.headers.update({'Accept-Datetime-Format': 'RFC3339'})

    

    def get_account(self):
        resp = self._request("GET", f"{self.url}/v3/accounts/{self.account_id}/summary")

        return resp['account']

    
    def get_initial_candles(self, instrument, from_date, granularity='M1'):
        now = datetime.now(timezone.utc)

        if granularity == 'D1':
            delta = timedelta(days=500)
        elif granularity == 'H1':
            delta = timedelta(days=100)
        else:
            delta = timedelta(days=3)

        data = []
        while from_date < now:
            to_date = from_date + delta
            if to_date > now:
                to_date = None

            data.extend(self.get_candles(instrument, from_date, to_date, granularity))

            from_date = from_date + delta
        
        return data
    

    def get_candles(self, instrument, from_date, to_date, granularity='M1'):
        params = {
            "price": "M",
            "granularity": granularity,
            "from": date_to_rfc3339(from_date)
        }

        if to_date is not None:
            params['to'] = date_to_rfc3339(to_date)
        else:
            params['count'] = 5000

        resp = self._request("GET", f"{self.url}/v3/instruments/{instrument}/candles", params=params)

        return [
            {
                'open_price': float(candle['mid']['o']),
                'high_price': float(candle['mid']['h']),
                'low_price': float(candle['mid']['l']),
                'close_price': float(candle['mid']['c']),
                'volume': candle['volume'],
                'timestamp': dateutil.parser.isoparse(candle['time'])
            }
            for candle in resp['candles']
        ]
    

    def get_ask_price(self, instrument):
        params = {
            "price": "A",
            "count": 1
        }
        resp = self._request("GET", f"{self.url}/v3/instruments/{instrument}/candles", params=params)

        return float(resp['candles'][0]['ask']['c'])
    

    def get_position_for_instrument(self, instrument):
        resp = self._request("GET", f"{self.url}/v3/accounts/{self.account_id}/positions/{instrument}")

        return {
            'short': abs(round(float(resp['position']['short']['units']))),
            'long': abs(round(float(resp['position']['long']['units'])))
        }


    def new_stop_order(self, instrument, units, entry, stop, profit1, profit2):
        units1 = round(units / 2)
        units2 = units - units1

        order1 = self._create_order('STOP', instrument, units1, entry, stop, profit1)
        order2 = self._create_order('STOP', instrument, units2, entry, stop, profit2)

        return (order1, order2)
    

    def _create_order(self, type, instrument, units, entry, stop, profit):
        url = f"{self.url}/v3/accounts/{self.account_id}/orders"
        body = {
            'order': {
                'type': type,
                'instrument': instrument,
                'units': str(units),
                'price': str(entry),
                'timeInForce': 'GTC',
                'stopLossOnFill': {
                    'price': str(stop),
                    'timeInForce': 'GTC',
                },
                'takeProfitOnFill': {
                    'price': str(profit),
                    'timeInForce': 'GTC',
                }
            }
        }
        logging.info(f"Sending create order request: {body}")

        return self._request("POST", url, json=body)
