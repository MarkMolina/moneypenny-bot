import StringIO
import json
import logging
import random
import urllib
import urllib2
import time
import math
import re

import requests


def _query(url, header):
    r = requests.post(url, data=header)
    if r.status_code == 200:
        return json.loads(r.text)['result']



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



def main(text, bot_on=False):
    if text.startswith('/'):
        if text.split(' ')[0][1:].upper() in BITT_ASSETPAIRS:
            # TODO: insert bittrex methods here
            pair = text.split(' ')[0][1:]
            bittrex = BittrexExchange()
            ticker = bittrex.getTicker(pair=pair)

            askPrice = float(ticker['Ask Price'])
            bidPrice = float(ticker['Bid Price'])
            price = (askPrice + bidPrice) / 2
            highPrice = float(ticker['High'])
            lowPrice = float(ticker['Low'])
            r = ""

            if len(text.split(' ')) > 1:
                if text.split(' ')[1] == 'fib':
                    print 'yo'
                    l_one = highPrice
                    l_two = highPrice - ((highPrice - lowPrice) * 0.236)
                    l_three = highPrice - ((highPrice - lowPrice) * 0.382)
                    l_four = highPrice - ((highPrice - lowPrice) * 0.5)
                    l_five = highPrice - ((highPrice - lowPrice) * 0.618)
                    l_six = highPrice - ((highPrice - lowPrice) * 0.786)
                    l_seven = lowPrice
                    l_eight = highPrice - ((highPrice - lowPrice) * 1.272)
                    l_nine = highPrice - ((highPrice - lowPrice) * 1.618)

                    r = '*{0}* 24h fib levels\n\n*0%*: {1}\n*23.6%*: {2}\n*38.2%*: {3}\n*50%*: {4}\n*61.8%*: {5}\n*78.6%*: {6}\n*100%*: {7}\n\n*127.2%*: {8}\n*161.8%*: {9}\n'.format(pair, l_one, l_two, l_three, l_four, l_five, l_six, l_seven, l_eight, l_nine)
                    print r
            else:
                r = '*{}* \n*Price:* {} \n*---* \n*High:* {} \n*Low:* {}'.format(pair, price, highPrice, lowPrice)
            if bot_on is True:
                reply(r)
            else:
                return r




if __name__ == '__main__':
    r=main('/btc-ltc fib')



    r
    r
    len('/btc-ltc fib'.split(' '))
    '/btc-ltc fib'.split(' ')[1]
