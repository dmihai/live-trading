import requests
from datetime import datetime, timezone, timedelta
import dateutil.parser

class Oanda:
    def __init__(self, api_key, url='https://api-fxpractice.oanda.com', date_format='RFC3339'):
        self.url = url

        self.sess = requests.Session()
        self.sess.headers.update({'Authorization': f"Bearer {api_key}"})
        self.sess.headers.update({'Accept-Datetime-Format': date_format})
    

    def get_initial_candles(self, instrument, from_date, granularity='M1'):
        now = datetime.now(timezone.utc)
        delta = timedelta(days=3)

        data = []
        while from_date < now:
            to_date = from_date + delta
            if to_date > now:
                to_date = None

            data_raw = self.get_candles(instrument, from_date, to_date, granularity)
            data.extend([
                {
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c']),
                    'volume': candle['volume'],
                    'time': dateutil.parser.isoparse(candle['time'])
                }
                for candle in data_raw['candles']
            ])

            from_date = from_date + delta
        
        return data
    

    def get_candles(self, instrument, from_date, to_date, granularity='M1'):
        params = {
            "price": "M",
            "granularity": granularity,
            "from": from_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }

        if to_date is not None:
            params['to'] = to_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            params['count'] = 5000
        
        resp = self.sess.get(f"{self.url}/v3/instruments/{instrument}/candles", params=params)
        return resp.json()
