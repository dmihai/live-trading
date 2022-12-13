import json
import signal
import logging
import time
import importlib
from datetime import date

from providers.oanda import Oanda
from trade.trade import Trade


def get_config(file):
    f = open(file)
    config = json.load(f)
    f.close()

    return config


def config_logging(config):
    filename = config['filename'].replace("%(today)s", str(date.today())) if config['output'] == 'file' else None
    level = getattr(logging, config['level'].upper())
    
    logging.basicConfig(filename=filename, format="%(asctime)s - %(levelname)s - %(message)s", level=level)


def stop_trading(signum, frame):
    global trades, is_running

    for trade in trades:
        trade.stop()
    
    is_running = False


config = get_config('config.json')
config_logging(config['logging'])
oanda_config = config['providers']['oanda']

trading_config = get_config('trading.json')

api = Oanda(oanda_config['api_key'], oanda_config['account_id'], url=oanda_config['url'])

trades = []
for item in trading_config:
    if not(item['enabled']):
        continue

    logging.info(f"Initialize {item['instrument']}")
    start_time = time.time()

    module = importlib.import_module("trade.strategies." + item['strategy'])
    class_ = getattr(module, item['strategy'])

    strategy = class_(item['instrument'], api)
    strategy.load_params(item['params'])

    trade = Trade(item['instrument'], api, strategy)

    try:
        trade.init_data()
    except Exception as e:
        logging.warning(f"Failed to initialize data for instrument {item['instrument']}")
    else:
        logging.info(f"{item['instrument']} init finished in {round(time.time() - start_time, 2)}s, {len(trade.df)} rows retrieved")
        
        trade.run()
        trades.append(trade)

is_running = True

signal.signal(signal.SIGINT, stop_trading)
signal.signal(signal.SIGTERM, stop_trading)

while is_running:
    pass
