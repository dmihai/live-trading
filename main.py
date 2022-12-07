import json
import signal
import logging
import time
from datetime import date

from providers.oanda import Oanda
from trade.trade import Trade

def get_config():
    f = open('config.json')
    config = json.load(f)
    f.close()

    return config

def stop_trading(signum, frame):
    global trades, is_running

    for trade in trades:
        trade.stop()
    
    is_running = False

logging.basicConfig(filename=f"log-{date.today()}.log", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

config = get_config()
oanda_config = config['providers']['oanda']

api = Oanda(oanda_config['api_key'], url=oanda_config['url'], date_format=oanda_config['date_format'])

instruments = ['EUR_USD', 'USD_JPY', 'NZD_CAD']
trades = []
for instrument in instruments:
    logging.info(f"Initialize {instrument}")
    start_time = time.time()
    trade = Trade(api, instrument)
    trade.init_data()
    logging.info(f"{instrument} init finished in {round(time.time() - start_time, 2)}s, {len(trade.df)} rows retrieved")
    trade.run()
    trades.append(trade)

is_running = True

signal.signal(signal.SIGINT, stop_trading)
signal.signal(signal.SIGTERM, stop_trading)

while is_running:
    pass
