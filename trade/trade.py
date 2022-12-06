from datetime import datetime, timezone, timedelta
import pandas as pd

class Trade:
    def __init__(self, api, instrument):
        self.api = api
        self.instrument = instrument
    
    def init_data(self):
        now = datetime.now(timezone.utc)
        from_date = now - timedelta(days=45)

        data = self.api.get_initial_candles(self.instrument, from_date, 'M1')
        index = [
            item['time']
            for item in data
        ]
        self.df = pd.DataFrame(data, index=index)
    
