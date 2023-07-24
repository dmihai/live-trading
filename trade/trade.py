from datetime import datetime, timezone, timedelta
import time
import threading
import logging
import pandas as pd

from trade.strategy import Strategy
from providers.oanda import Oanda
from providers.xtb import XTB
from utils.time import get_time_elapsed


class Trade:
    def __init__(self, instrument, api: Oanda | XTB, strategy: Strategy, history_days=30):
        self.instrument = instrument
        self.api = api
        self.strategy = strategy
        self.granularity = 'M1'
        self.interval = 60  # seconds
        self.history_days = history_days
    

    def init_data(self):
        now = datetime.now(timezone.utc)
        from_date = now - timedelta(days=self.history_days)

        data = self.api.get_initial_candles(self.instrument, from_date, self.granularity)
        self.df = self.__get_dataframe(data)
    

    def run(self):
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()
    

    def stop(self):
        self.stopEvent.set()
    

    def __loop(self):
        logging.debug(f"Start loop for {self.instrument}")
        start_time = time.time()

        try:
            from_date = self.df.tail(1).timestamp[0]
            data = self.api.get_candles(self.instrument, from_date, None, self.granularity)
            
            new_df = self.__get_dataframe(data)

            self.df.update(new_df)
            self.df = self.df.combine_first(new_df)
            self.strategy.load_data(self.df)
            self.strategy.trade()
        except Exception as e:
            logging.warning(f"Loop failed for {self.instrument} with {e}")
        else:
            logging.debug(f"Loop finished for {self.instrument} in {get_time_elapsed(start_time)}s")
    

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
