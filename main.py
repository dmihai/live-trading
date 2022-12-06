import json

from providers.oanda import Oanda
from trade.trade import Trade

def get_config():
    f = open('config.json')
    config = json.load(f)
    f.close()

    return config

config = get_config()
oanda_config = config['providers']['oanda']

api = Oanda(oanda_config['api_key'], url=oanda_config['url'], date_format=oanda_config['date_format'])
trade = Trade(api, "EUR_USD")
trade.init_data()
print(trade.df)
