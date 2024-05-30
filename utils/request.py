import json

import requests
from requests.adapters import Retry, HTTPAdapter
import logging


class BaseRequests:

    def __init__(self):
        self.session = requests.Session()
        retries = Retry(total=10000,
                        backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504, 429],
                        allowed_methods=None)
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.proxies = None
        self.cookies = None

    def request(self, method, *args, **kwargs):
        kwargs.update({'proxies': self.proxies})
        response = self.session.request(method, *args, **kwargs)
        try:
            response.raise_for_status()
        except Exception as e:
            logging.error(json.dumps({"request": dict(method=method, args=args, kwargs=kwargs),
                                      "response": response.text,
                                      "exception": str(e)}))
            raise e
        return response

    def get(self, *args, **kwargs):
        return self.request('get', cookies=self.cookies, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('post', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('delete', *args, **kwargs)