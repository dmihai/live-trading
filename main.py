import json
import signal
import logging
import time
from datetime import date

from providers.oanda import Oanda
from trade.trade import Trade
from trade.strategies.HighFreqReversal import HighFreqReversal

def get_config():
    f = open('config.json')
    config = json.load(f)
    f.close()

    return config


def config_logging(config):
    filename = config['filename'].replace("%(today)s", str(date.today())) if config['output'] == 'file' else None
    level = logging.INFO
    if config['level'] == 'debug':
        level = logging.DEBUG
    elif config['level'] == 'warning':
        level = logging.WARNING
    elif config['level'] == 'error':
        level = logging.ERROR
    
    logging.basicConfig(filename=filename, format="%(asctime)s - %(levelname)s - %(message)s", level=level)


def stop_trading(signum, frame):
    global trades, is_running

    for trade in trades:
        trade.stop()
    
    is_running = False


config = get_config()
config_logging(config['logging'])
oanda_config = config['providers']['oanda']

api = Oanda(oanda_config['api_key'], oanda_config['account_id'], url=oanda_config['url'])
strategy = HighFreqReversal()

instruments = ['EUR_USD', 'USD_JPY', 'NZD_CAD']
trades = []
for instrument in instruments:
    logging.info(f"Initialize {instrument}")
    start_time = time.time()
    trade = Trade(instrument, api, strategy)
    trade.init_data()
    logging.info(f"{instrument} init finished in {round(time.time() - start_time, 2)}s, {len(trade.df)} rows retrieved")
    trade.run()
    trades.append(trade)

is_running = True

signal.signal(signal.SIGINT, stop_trading)
signal.signal(signal.SIGTERM, stop_trading)

while is_running:
    pass
