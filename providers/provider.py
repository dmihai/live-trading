import requests
import logging
import time


class Provider:
    def __init__(self, url):
        self.url = url
        self.sess = requests.Session()


    def _request(self, verb, url, params={}, json=None):
        resp = self.__do_request(verb, url, params=params, json=json)
        resp.raise_for_status()

        return resp.json()
    

    def __do_request(self, verb, url, params={}, json=None):
        i = 0
        while True:
            try:
                resp = self.sess.request(verb, url, params=params, json=json)
                return resp
            except Exception as e:
                logging.warning(f"API request error {e}")
                time.sleep(1)

                i += 1
                if i >= 10:
                    raise
