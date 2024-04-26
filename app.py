import hashlib
import hmac
import time
import requests
import websocket
import json
import base64

class KrakenExchange:
    def __init__(self, api_key, api_secret):
        self.api_url = 'https://api.kraken.com'
        self.api_key = api_key
        self.api_secret = api_secret

    def _generate_signature(self, urlpath, data):
        postdata = '&'.join([f"{key}={value}" for key, value in data.items()]).encode()
        encoded = (str(data['nonce']) + postdata.decode()).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.api_secret),
                            message, hashlib.sha512)
        return base64.b64encode(signature.digest()).decode()

    def _api_request(self, path, data):
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._generate_signature(path, data)
        }
        response = requests.post(self.api_url + path, data=data, headers=headers)
        return response.json()

    def get_account_balance(self):
        path = '/0/private/Balance'
        data = {
            'nonce': str(int(time.time() * 1000)),
        }
        return self._api_request(path, data)

    def get_ohlcv_data(self, pair, interval):
        path = '/0/public/OHLC'
        data = {
            'pair': pair,
            'interval': interval
        }
        response = requests.get(self.api_url + path, params=data)
        return response.json()


    def place_order(self, pair, type, ordertype, volume, price=None):
        path = '/0/private/AddOrder'
        data = {
            'nonce': str(int(time.time() * 1000)),
            'pair': pair,
            'type': type,
            'ordertype': ordertype,
            'volume': str(volume),
        }
        if price:
            data['price'] = str(price)
        return self._api_request(path, data)
        
    def on_message(ws, message):
        data = json.loads(message)
        print("New mid-price:", (float(data['b'][0][0]) + float(data['a'][0][0])) / 2)

    def setup_midprice_feed(self, pair):
        ws = websocket.WebSocketApp("wss://ws.kraken.com/",
                                    on_message=self.on_message)
        ws.on_open = lambda ws: ws.send(json.dumps({
            "event": "subscribe",
            "pair": [pair],
            "subscription": {"name": "ticker"}
        }))
        ws.run_forever()
