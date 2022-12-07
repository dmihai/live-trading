from datetime import datetime, timezone, timedelta
import time
import threading
import pandas as pd

class Trade:
    def __init__(self, api, instrument):
        self.api = api
        self.instrument = instrument
        self.granularity = 'M1'
        self.interval = 60  # seconds
    
    def init_data(self):
        now = datetime.now(timezone.utc)
        from_date = now - timedelta(days=45)

        data = self.api.get_initial_candles(self.instrument, from_date, self.granularity)
        index = [
            item['time']
            for item in data
        ]
        self.df = pd.DataFrame(data, index=index)
    
    def run(self):
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()
    
    def stop(self):
        self.stopEvent.set()
    
    def __loop(self):
        from_date = self.df.tail(1).time[0]
        data = self.api.get_candles(self.instrument, from_date, None, self.granularity)
        
        index = [
            item['time']
            for item in data
        ]
        new_df = pd.DataFrame(data, index=index)

        self.df.update(new_df)
        self.df = self.df.combine_first(new_df)
        print(self.instrument, "Loop")
        print(self.df)
    
    def __setInterval(self) :
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()) :
            nextTime += self.interval
            self.__loop()
    
