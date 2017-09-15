import json
import requests
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()


# ===== Kraken Exchange methods & classes ======

PUBLIC_URLS = {
    'time': 'https://api.kraken.com/0/public/Time',
    'assets': 'https://api.kraken.com/0/public/Assets',
    'assetPairs': 'https://api.kraken.com/0/public/AssetPairs',
    'ticker': 'https://api.kraken.com/0/public/Ticker',
    'ohlc': 'https://api.kraken.com/0/public/OHLC',
    'orderBook': 'https://api.kraken.com/0/public/Depth',
    'recentTrades': 'https://api.kraken.com/0/public/Trades',
    'spread': 'https://api.kraken.com/0/public/Spread',
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

ASSETS = ['DASH', 'EOS', 'ETC', 'ETH', 'GNO', 'ICN', 'LTC', 'MLN', 'REP', 'USDT',
          'XBT', 'XDG', 'XLM', 'XMR', 'XRP', 'ZEC', 'BCH']

ASSETPAIRS = {
    'DASHEUR': 'DASHEUR',
    'DASHUSD': 'DASHUSD',
    'DASHXBT': 'DASHXBT',
    'EOSETH': 'EOSETH',
    'EOSUSD': 'EOSUSD',
    'EOSXBT': 'EOSXBT',
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
    'ZECXBT': 'XZECXXBT',
    'BCHEUR': 'BCHEUR',
    'BCHUSD': 'BCHUSD',
    'BCHXBT': 'BCHXBT',
}

MAXREQUESTS = 15


def _query(url, header):
    r = requests.post(url, data=header)
    if r.status_code == 200:
        return json.loads(r.text)['result']


class KrakenExchange(object):
    """
    Holds all methods for fetching Assets, Assetpairs and current Ticker
    values from the Kraken Exchange.
    Time Skew can be displayed by requesting server time.
    """
    def __init__(self):
        super(KrakenExchange, self).__init__()

    def query_public(self, type, header=None):
        return _query(PUBLIC_URLS[type], header)

    def getServerTime(self):
        serverTime = self.query_public('time')
        if type(serverTime) == ValueError:
            return serverTime.message
        self.serverTime = serverTime
        return self.serverTime

    def getServerSkew(self):
        self.serverSkew = time.time() - self.getServerTime()['unixtime']
        return self.serverSkew

    def getOrderBook(self, pair):
        header = dict(
            pair=pair,
            count=10,
        )
        r = self.query_public('orderBook', header)
        return r

    def getTicker(self, pair):
        header = {'pair': pair} if pair else None
        r = self.query_public('ticker', header)
        if type(r) == ValueError:
            return r.message
        self.ticker = {}
        ticker = r[pair]
        for t in ticker.keys():
            self.ticker[TICKER_MAPPING[t]] = ticker[t]
        return self.ticker





# ===== Bittrex Exchange methods & classes ======
BITT_PUBLIC_URLS = {
    # hold open markets, assets and pairs.
    'markets': 'https://bittrex.com/api/v1.1/public/getmarkets',
    'currencies': 'https://bittrex.com/api/v1.1/public/getcurrencies ',
    # Just the current price and bid ask.
    'ticker': 'https://bittrex.com/api/v1.1/public/getticker',
    # > 1 market 24h summary, current high-low etc
    'summary': 'https://bittrex.com/api/v1.1/public/getmarketsummary',
    # > 1 market 24h summary, current high-low etc
    'summaries': 'https://bittrex.com/api/v1.1/public/getmarketsummaries',
    'orderBook': 'https://bittrex.com/api/v1.1/public/getorderbook',
    'history': 'https://bittrex.com/api/v1.1/public/getmarkethistory'
}

BITT_TICKER_MAPPING = {
    'MarketName': 'Pair',
    'High': 'High',
    'Low': 'Low',
    'Volume': 'Volume',
    'Last': 'Last',
    'BaseVolume': 'Base Volume',
    'Bid': 'Bid Price',
    'Ask': 'Ask Price',
    'OpenBuyOrders': '# Buy Orders',
    'OpenSellOrders': '# Sell Orders'
}

BITT_ASSETPAIRS = [
     u'BTC-LTC',
     u'BTC-DOGE',
     u'BTC-VTC',
     u'BTC-PPC',
     u'BTC-FTC',
     u'BTC-RDD',
     u'BTC-NXT',
     u'BTC-DASH',
     u'BTC-POT',
     u'BTC-BLK',
     u'BTC-EMC2',
     u'BTC-XMY',
     u'BTC-AUR',
     u'BTC-EFL',
     u'BTC-GLD',
     u'BTC-SLR',
     u'BTC-PTC',
     u'BTC-GRS',
     u'BTC-NLG',
     u'BTC-RBY',
     u'BTC-XWC',
     u'BTC-MONA',
     u'BTC-THC',
     u'BTC-ENRG',
     u'BTC-ERC',
     u'BTC-NAUT',
     u'BTC-VRC',
     u'BTC-CURE',
     u'BTC-XBB',
     u'BTC-XMR',
     u'BTC-CLOAK',
     u'BTC-START',
     u'BTC-KORE',
     u'BTC-XDN',
     u'BTC-TRUST',
     u'BTC-NAV',
     u'BTC-XST',
     u'BTC-BTCD',
     u'BTC-VIA',
     u'BTC-UNO',
     u'BTC-PINK',
     u'BTC-IOC',
     u'BTC-CANN',
     u'BTC-SYS',
     u'BTC-NEOS',
     u'BTC-DGB',
     u'BTC-BURST',
     u'BTC-EXCL',
     u'BTC-SWIFT',
     u'BTC-DOPE',
     u'BTC-BLOCK',
     u'BTC-ABY',
     u'BTC-BYC',
     u'BTC-XMG',
     u'BTC-BLITZ',
     u'BTC-BAY',
     u'BTC-BTS',
     u'BTC-FAIR',
     u'BTC-SPR',
     u'BTC-VTR',
     u'BTC-XRP',
     u'BTC-GAME',
     u'BTC-COVAL',
     u'BTC-NXS',
     u'BTC-XCP',
     u'BTC-BITB',
     u'BTC-GEO',
     u'BTC-FLDC',
     u'BTC-GRC',
     u'BTC-FLO',
     u'BTC-NBT',
     u'BTC-MUE',
     u'BTC-XEM',
     u'BTC-CLAM',
     u'BTC-DMD',
     u'BTC-GAM',
     u'BTC-SPHR',
     u'BTC-OK',
     u'BTC-SNRG',
     u'BTC-PKB',
     u'BTC-CPC',
     u'BTC-AEON',
     u'BTC-ETH',
     u'BTC-GCR',
     u'BTC-TX',
     u'BTC-BCY',
     u'BTC-EXP',
     u'BTC-INFX',
     u'BTC-OMNI',
     u'BTC-AMP',
     u'BTC-AGRS',
     u'BTC-XLM',
     u'BTC-BTA',
     u'USDT-BTC',
     u'BITCNY-BTC',
     u'BTC-CLUB',
     u'BTC-VOX',
     u'BTC-EMC',
     u'BTC-FCT',
     u'BTC-MAID',
     u'BTC-EGC',
     u'BTC-SLS',
     u'BTC-RADS',
     u'BTC-DCR',
     u'BTC-SAFEX',
     u'BTC-BSD',
     u'BTC-XVG',
     u'BTC-PIVX',
     u'BTC-XVC',
     u'BTC-MEME',
     u'BTC-STEEM',
     u'BTC-2GIVE',
     u'BTC-LSK',
     u'BTC-PDC',
     u'BTC-BRK',
     u'BTC-DGD',
     u'ETH-DGD',
     u'BTC-WAVES',
     u'BTC-RISE',
     u'BTC-LBC',
     u'BTC-SBD',
     u'BTC-BRX',
     u'BTC-DRACO',
     u'BTC-ETC',
     u'ETH-ETC',
     u'BTC-STRAT',
     u'BTC-UNB',
     u'BTC-SYNX',
     u'BTC-TRIG',
     u'BTC-EBST',
     u'BTC-VRM',
     u'BTC-SEQ',
     u'BTC-XAUR',
     u'BTC-SNGLS',
     u'BTC-REP',
     u'BTC-SHIFT',
     u'BTC-ARDR',
     u'BTC-XZC',
     u'BTC-NEO',
     u'BTC-ZEC',
     u'BTC-ZCL',
     u'BTC-IOP',
     u'BTC-DAR',
     u'BTC-GOLOS',
     u'BTC-HKG',
     u'BTC-UBQ',
     u'BTC-KMD',
     u'BTC-GBG',
     u'BTC-SIB',
     u'BTC-ION',
     u'BTC-LMC',
     u'BTC-QWARK',
     u'BTC-CRW',
     u'BTC-SWT',
     u'BTC-TIME',
     u'BTC-MLN',
     u'BTC-ARK',
     u'BTC-DYN',
     u'BTC-TKS',
     u'BTC-MUSIC',
     u'BTC-DTB',
     u'BTC-INCNT',
     u'BTC-GBYTE',
     u'BTC-GNT',
     u'BTC-NXC',
     u'BTC-EDG',
     u'BTC-LGD',
     u'BTC-TRST',
     u'ETH-GNT',
     u'ETH-REP',
     u'USDT-ETH',
     u'ETH-WINGS',
     u'BTC-WINGS',
     u'BTC-RLC',
     u'BTC-GNO',
     u'BTC-GUP',
     u'BTC-LUN',
     u'ETH-GUP',
     u'ETH-RLC',
     u'ETH-LUN',
     u'ETH-SNGLS',
     u'ETH-GNO',
     u'BTC-APX',
     u'BTC-TKN',
     u'ETH-TKN',
     u'BTC-HMQ',
     u'ETH-HMQ',
     u'BTC-ANT',
     u'ETH-TRST',
     u'ETH-ANT',
     u'BTC-SC',
     u'ETH-BAT',
     u'BTC-BAT',
     u'BTC-ZEN',
     u'BTC-1ST',
     u'BTC-QRL',
     u'ETH-1ST',
     u'ETH-QRL',
     u'BTC-CRB',
     u'ETH-CRB',
     u'ETH-LGD',
     u'BTC-PTOY',
     u'ETH-PTOY',
     u'BTC-MYST',
     u'ETH-MYST',
     u'BTC-CFI',
     u'ETH-CFI',
     u'BTC-BNT',
     u'ETH-BNT',
     u'BTC-NMR',
     u'ETH-NMR',
     u'ETH-TIME',
     u'ETH-LTC',
     u'ETH-XRP',
     u'BTC-SNT',
     u'ETH-SNT',
     u'BTC-DCT',
     u'BTC-XEL',
     u'BTC-MCO',
     u'ETH-MCO',
     u'BTC-ADT',
     u'ETH-ADT',
     u'BTC-FUN',
     u'ETH-FUN',
     u'BTC-PAY',
     u'ETH-PAY',
     u'BTC-MTL',
     u'ETH-MTL',
     u'BTC-STORJ',
     u'ETH-STORJ',
     u'BTC-ADX',
     u'ETH-ADX',
     u'ETH-DASH',
     u'ETH-SC',
     u'ETH-ZEC',
     u'USDT-ZEC',
     u'USDT-LTC',
     u'USDT-ETC',
     u'USDT-XRP',
     u'BTC-OMG',
     u'ETH-OMG',
     u'BTC-CVC',
     u'ETH-CVC',
     u'BTC-PART',
     u'BTC-QTUM',
     u'ETH-QTUM',
     u'ETH-XMR',
     u'ETH-XEM',
     u'ETH-XLM',
     u'ETH-NEO',
     u'USDT-XMR',
     u'USDT-DASH',
     u'ETH-BCC',
     u'USDT-BCC',
     u'BTC-BCC',
     u'USDT-NEO',
     u'ETH-WAVES',
     u'ETH-STRAT',
     u'ETH-DGB',
     u'ETH-FCT',
     u'ETH-BTS']


# TODO: retrieve all pairs from the `getmarket` data. Pairs will have "-"
#       which will be handy for separation.


class BittrexExchange(object):
    """
    Holds all methods for fetching:
     - Assets, Assetpairs, Current Ticker, 24h summary, order book, and history
    values and current Ticker
    values from the Kraken Exchange.
    Time Skew can be displayed by requesting server time.
    """
    def __init__(self):
        super(BittrexExchange, self).__init__()

    def query_public(self, type, header=None):
        return _query(BITT_PUBLIC_URLS[type], header)

    def getTicker(self, pair):
        header = {'market': pair} if pair else None
        r = self.query_public('summary', header)
        if type(r) == ValueError:
            return r.message
        self.ticker = {}

        ticker = r[0]
        # print(ticker)
        for t in ticker.keys():
            if t in BITT_TICKER_MAPPING.keys():
                self.ticker[BITT_TICKER_MAPPING[t]] = ticker[t]
        return self.ticker

    def getmarkets(self, type, header=None):
        header = None
        r = self.query_public('markets', header)
        self.markets = []
        markets = r
        for i, cont in enumerate(markets):
            self.markets.append(markets[i]["MarketName"])
        return self.markets
