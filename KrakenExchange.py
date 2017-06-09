import requests
import time
import json

PUBLIC_URLS = {
    'time': 'https://api.kraken.com/0/public/Time',
    'assets': 'https://api.kraken.com/0/public/Assets',
    'assetPairs': 'https://api.kraken.com/0/public/AssetPairs',
    'ticker': 'https://api.kraken.com/0/public/Ticker',
}

TICKER_MAPPING = {
    'a': 'Ask Price',
    'b': 'Bid Price',
    'c': 'Last Trade',
    'v': 'Volume',
    'p': 'Volume weighted avg',
    't': '# Trades',
    'l': 'Low',
    'h': 'High',
    'o': 'Opening Price',
}

ASSETS = {
    'DASHEUR': 'DASHEUR',
    'DASHUSD': 'DASHUSD',
    'DASHXBT': 'DASHXBT',
    'ETCETH': 'XETCXETH',
    'ETCEUR': 'XETCZEUR',
    'ETCUSD': 'XETCZUSD',
    'ETCXBT': 'XETCXXBT',
    'ETHCAD': 'XETHZCAD',
    'ETHEUR': 'XETHZEUR',
    'ETHGBP': 'XETHZGBP',
    'ETHJPY': 'XETHZJPY',
    'ETHUSD': 'XETHZUSD',
    'ETHXBT': 'XETHXXBT',
    'GNOETH': 'GNOETH',
    'GNOEUR': 'GNOEUR',
    'GNOUSD': 'GNOUSD',
    'GNOXBT': 'GNOXBT',
    'ICNETH': 'XICNXETH',
    'ICNXBT': 'XICNXXBT',
    'LTCEUR': 'XLTCZEUR',
    'LTCUSD': 'XLTCZUSD',
    'LTCXBT': 'XLTCXXBT',
    'MLNETH': 'XMLNXETH',
    'MLNXBT': 'XMLNXXBT',
    'REPETH': 'XREPXETH',
    'REPEUR': 'XREPZEUR',
    'REPUSD': 'XREPZUSD',
    'REPXBT': 'XREPXXBT',
    'USDTUSD': 'USDTZUSD',
    'XBTCAD': 'XXBTZCAD',
    'XBTEUR': 'XXBTZEUR',
    'XBTGBP': 'XXBTZGBP',
    'XBTJPY': 'XXBTZJPY',
    'XBTUSD': 'XXBTZUSD',
    'XDGXBT': 'XXDGXXBT',
    'XLMEUR': 'XXLMZEUR',
    'XLMUSD': 'XXLMZUSD',
    'XLMXBT': 'XXLMXXBT',
    'XMREUR': 'XXMRZEUR',
    'XMRUSD': 'XXMRZUSD',
    'XMRXBT': 'XXMRXXBT',
    'XRPCAD': 'XXRPZCAD',
    'XRPEUR': 'XXRPZEUR',
    'XRPJPY': 'XXRPZJPY',
    'XRPUSD': 'XXRPZUSD',
    'XRPXBT': 'XXRPXXBT',
    'ZECEUR': 'XZECZEUR',
    'ZECUSD': 'XZECZUSD',
    'ZECXBT': 'XZECXXBT'
}

def _query(url, header):
    r = requests.post(url)
    if r.status_code == 200:
        return json.loads(r.text)['result']

def query_public(type, header=None):
    assert type in PUBLIC_URLS.keys(), "Type is not recognized in any public API"
    return _query(PUBLIC_URLS[type], header)


class KrakenExchange(object):
    """
    Holds all methods for fetching Assets, Assetpairs and current Ticker
    values from the Kraken Exchange.

    Time Skew can be displayed by requesting server time.
    """
    def __init__(self):
        super(KrakenExchange, self).__init__()
        self.getServerTime()
        # self.determineServerSkew()

    def getServerTime(self):
        self.serverTime = query_public('time')
        return self.serverTime

    def getServerSkew(self):
        self.serverSkew = time.time() - self.getServerTime()['unixtime']
        return self.serverSkew

    def getAssets(self, asset=None):
        header = {'asset': asset} if asset else None
        self.assets = query_public('assets', header)
        return self.assets

    def getAssetPairs(self):
        self.assetPairs = {}
        pairs = query_public('assetPairs')
        for pair in pairs.keys():
            name = pairs[pair]['altname']
            if not name[-2:] == '.d':
                self.assetPairs[pairs[pair]['altname']] = pair
        return self.assetPairs

    def getTicker(self, pair):
        r = requests.post(PUBLIC_URLS['ticker'], data={'pair': pair})
        self.ticker = {}
        ticker = json.loads(r.text)['result'][pair]
        for t in ticker.keys():
            self.ticker[TICKER_MAPPING[t]] = ticker[t]
        return self.ticker
