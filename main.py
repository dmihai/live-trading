import json
import signal
import logging
import time
import importlib
import psutil
import os
import sys
from datetime import date

from providers.oanda import Oanda
from trade.trade import Trade
from utils.time import get_current_time


def is_running(script):
    for q in psutil.process_iter():
        if q.name().startswith('python'):
            if len(q.cmdline()) > 1 and script in q.cmdline()[1] and q.pid != os.getpid():
                return True

    return False


def get_config(file):
    f = open(file)
    config = json.load(f)
    f.close()

    return config


def config_logging(config):
    filename = config['filename'].replace("%(today)s", str(date.today())) if config['output'] == 'file' else None
    level = getattr(logging, config['level'].upper())
    
    logging.basicConfig(filename=filename, format="%(asctime)s - %(levelname)s - %(message)s", level=level)


def stop_trading(signum=None, frame=None):
    global trades, is_running

    for trade in trades:
        trade.stop()
    
    is_running = False


def is_trading_time():
    now = get_current_time()
    weekday = now.weekday()

    if weekday <= 3:  # Mon-Thu
        return True
    if weekday == 6 and now.hour >= 21:  # Sun after 21:00
        return True
    if weekday == 4 and now.hour < 14:  # Fri before 14:00
        return True
    
    return False


if is_running(sys.argv[0]):
    print("Script is already running")
    sys.exit()

config = get_config('config.json')
config_logging(config['logging'])

if not(is_trading_time()):
    logging.info("Cannot trade outside the trading session")
    sys.exit()

oanda_config = config['providers']['oanda']
api = Oanda(oanda_config['api_key'], oanda_config['account_id'], url=oanda_config['url'])

trading_config = get_config('trading.json')

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
    time.sleep(0.1)

    if not(is_trading_time()):
        logging.info('Outside the trading session, stopping now')
        stop_trading()
    
logging.info("The script is no longer running")
