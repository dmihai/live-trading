import logging

from providers.xtbAPIConnector import APIClient, APIStreamClient, loginCommand


class XTB():
    def __init__(self, user_id, password, address='xapi.xtb.com', port=5124, streaming_port=5125):
        client = APIClient(address=address, port=port)
        loginResponse = client.execute(loginCommand(userId=user_id, password=password))

        if(loginResponse['status'] == False):
            logging.error('Login failed. Error code: {0}'.format(loginResponse['errorCode']))
            return

        self.ssid = loginResponse['streamSessionId']
        self.sclient = APIStreamClient(ssId=self.ssid, address=address, port=streaming_port)
    

    def get_account(self):
        pass

    
    def get_initial_candles(self, instrument, from_date, granularity='M1'):
        pass
    

    def get_candles(self, instrument, from_date, to_date, granularity='M1'):
        pass
    

    def get_ask_price(self, instrument):
        pass
    

    def get_position_for_instrument(self, instrument):
        pass


    def new_stop_order(self, instrument, units, entry, stop, profit1, profit2):
        pass
