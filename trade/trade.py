from datetime import datetime, timezone, timedelta
import time
import threading
import logging
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
        self.df = self.__get_dataframe(data)
    
    def run(self):
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()
    
    def stop(self):
        self.stopEvent.set()
    
    def __loop(self):
        logging.info(f"Start loop for {self.instrument}")
        start_time = time.time()
        from_date = self.df.tail(1).time[0]
        data = self.api.get_candles(self.instrument, from_date, None, self.granularity)
        
        new_df = self.__get_dataframe(data)

        self.df.update(new_df)
        self.df = self.df.combine_first(new_df)
        logging.info(f"Loop finised for {self.instrument} in {round(time.time() - start_time, 2)}s")
    
    def __setInterval(self) :
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()) :
            nextTime += self.interval
            self.__loop()
    

    def __get_dataframe(self, data):
        index = [
            item['timestamp']
            for item in data
        ]

        return pd.DataFrame(data, index=index)
