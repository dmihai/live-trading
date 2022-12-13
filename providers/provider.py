import requests


class Provider:
    def __init__(self, url):
        self.url = url
        self.sess = requests.Session()


    def _do_request(self, verb, url, params={}, json=None):
        resp = self.sess.request(verb, url, params=params, json=json)
        resp.raise_for_status()

        return resp.json()
