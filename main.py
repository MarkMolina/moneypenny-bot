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
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()

# sending images
try:
    from PIL import Image
except:
    pass
import multipart

# standard app engineimports
from google.appengine.api import urlfetch
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.api.taskqueue import TaskRetryOptions
import webapp2

TOKEN = '363749995:AAEMaasMVLSPqSuSr1MiEFcgQH_Yn88hlbg'

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

urlfetch.set_default_fetch_deadline(60)

ALERTS = set()


def deffered_track_pair_price(pair, current_price, target_price, chat_id, message_id):
    alert_key = (pair, target_price)
    logging.info("Checking price alert..{} if {}".format(pair, target_price))
    kraken = KrakenExchange()
    ticker = kraken.getTicker(pair=ASSETPAIRS[pair])
    askPrice = float(ticker['Ask Price'][0])
    bidPrice = float(ticker['Bid Price'][0])
    live_price = (askPrice + bidPrice) / 2
    target_price = float(target_price)
    if current_price < target_price and live_price >= target_price:
        ALERTS.remove(alert_key)
        reply_message(
            chat_id=chat_id,
            message_id=message_id,
            msg="{} just hit {}!".format(
                pair, live_price
            )
        )
    elif current_price > target_price and live_price <= target_price:
        ALERTS.remove(alert_key)
        reply_message(
            chat_id=chat_id,
            message_id=message_id,
            msg="{} just hit {}!".format(
                pair, live_price
            )
        )
    else:
        raise Exception("Alert not hit, fail task so it is retried")


def track_pair_price(pair, current_price, target_price, chat_id, message_id):
    ALERTS.add(
        (pair, target_price)
    )

    deferred.defer(
        deffered_track_pair_price,
        pair, current_price, target_price, chat_id, message_id,
        _retry_options=TaskRetryOptions(
            min_backoff_seconds=60,
            task_age_limit=86400
        ) # 1 day
    )


# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)


# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False


# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


def reply_message(chat_id, message_id, msg=None, img=None):
    resp = ''

    try:
        if msg:
            resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                'chat_id': str(chat_id),
                'text': msg.encode('utf-8'),
                'disable_web_page_preview': 'true',
                'reply_to_message_id': str(message_id),
                'parse_mode': 'Markdown'
            })).read()
        elif img:
            resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                ('chat_id', str(chat_id)),
                ('reply_to_message_id', str(message_id)),
            ], [
                ('photo', 'image.jpg', img),
            ])
        else:
            logging.error('no msg or img specified')
            resp = None
    except Exception as exc:
        logging.error("ERROR %s" % exc)
        pass

    logging.info('send response:')
    logging.info(resp)


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        try:
            message = body['message']
        except:
            message = body['edited_message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        def reply(msg=None, img=None):
            reply_message(msg=msg, img=img, chat_id=chat_id, message_id=message_id)

        if not text:
            logging.info('no text')
            return

        if text.startswith('/'):
            text_kraken = re.sub('(\/btc)', '/xbt', text)
            text_kraken = re.sub('(btc$)', 'xbt', text)
            text_kraken = re.sub('(btc\s+)', 'xbt ', text)
            if text == '/start':
                reply('Bot enabled')
                setEnabled(chat_id, True)
            if text == '/alerts':
                reply(
                    "*Alerts*\n{}".format(
                        "\n".join([
                            "{}: {}".format(pair, price)
                            for pair, price in ALERTS
                        ])
                    )
                )

            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)
            elif text == '/rules':
                reply('1. You do not talk about WHALE HUNTERS \n2. You DO NOT talk about WHALE HUNTERS \n3. Master level of TA skills required \n3.141592 Bring pie \n4. Inactive members will be banned')
            elif text == '/image':
                img = Image.new('RGB', (512, 512))
                base = random.randint(0, 16777216)
                pixels = [base+i*j for i in range(512) for j in range(512)]
                img.putdata(pixels)
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue())
            elif text == '/help' or text == '/options':
                r = '/rules : show rules\n/image : generate an image\n/time(s) : get server time\n/assets : list of assets\n/pairs : list of all pairs (long)\n/<asset> : show this assets pairs\n/<assetpair> : show assetpairs price\n/alerts : show alerts'
                reply(r)
            elif text == '/time' or text == '/times':
                time = KrakenExchange().getServerTime()['rfc1123']
                r = 'Kraken server time: {}'.format(time)
                reply(r)
            elif text == '/assets':
                r = 'Reply with /<asset> to get its pairs\n{}'.format(', '.join(ASSETS))
                reply(r)
            elif text == '/pairs':
                assets = ASSETPAIRS.keys()
                assets.sort()
                r = 'Reply with /<assetpair> to get bid/ask prices\n{}'.format(', '.join(assets))
                reply(r)
            elif text == '/magic':
                r = 'https://media.giphy.com/media/12NUbkX6p4xOO4/giphy.gif'
                reply(r)
            elif text[1:].upper() in ASSETS:
                pairs = []
                for pair in ASSETPAIRS:
                    if pair[:3] == text[1:].upper()[:3]:
                        pairs.append(pair)
                r = 'Reply with /<assetpair> to get bid/ask prices\n{}'.format(', '.join(pairs))
                reply(r)

            elif text_kraken.split(' ')[0][1:].upper() in ASSETPAIRS.keys():
                pair = text_kraken.split(' ')[0][1:].upper()
                kraken = KrakenExchange()
                ticker = kraken.getTicker(pair=ASSETPAIRS[pair])
                askPrice = float(ticker['Ask Price'][0])
                bidPrice = float(ticker['Bid Price'][0])
                price = (askPrice + bidPrice) / 2
                highPrice = float(ticker['High'][0])
                lowPrice = float(ticker['Low'][0])
                # time = kraken.serverTime['rfc1123']
                r = ""
                if len(text_kraken.split(' ')) > 1:
                    if text_kraken.split(' ')[1] == 'fib':
                        l_one = highPrice
                        l_two = highPrice - ((highPrice - lowPrice) * 0.236)
                        l_three = highPrice - ((highPrice - lowPrice) * 0.382)
                        l_four = highPrice - ((highPrice - lowPrice) * 0.5)
                        l_five = highPrice - ((highPrice - lowPrice) * 0.618)
                        l_six = highPrice - ((highPrice - lowPrice) * 0.786)
                        l_seven = lowPrice
                        l_eight = highPrice - ((highPrice - lowPrice) * 1.272)
                        l_nine = highPrice - ((highPrice - lowPrice) * 1.618)

                        r = '*KRAKEN:{0}* 24h fib levels\n\n*0%*: {1}\n*23.6%*: {2}\n*38.2%*: {3}\n*50%*: {4}\n*61.8%*: {5}\n*78.6%*: {6}\n*100%*: {7}\n\n*127.2%*: {8}\n*161.8%*: {9}\n'.format(pair, l_one, l_two, l_three, l_four, l_five, l_six, l_seven, l_eight, l_nine)
                    if text_kraken.split(' ')[1] == 'book':
                        order_book = kraken.getOrderBook(pair=ASSETPAIRS[pair])
                        book = order_book[ASSETPAIRS[pair]]
                        r = "*OrderBook* KRAKEN:{0} \n*Asks*\n{1}\n\n*Bids*\n{2}".format(
                            pair,
                            "\n".join(
                                ["{} {}".format(ask[0], ask[1]) for ask in book['asks'][:10]]
                            ),
                            "\n".join(
                                ["{} {}".format(bid[0], bid[1]) for bid in book['bids'][:10]]
                            ),
                        )
                    if text_kraken.split(' ')[1] == 'alert':
                        try:
                            target_price = text_kraken.split(' ')[2]
                            track_pair_price(pair, price, target_price, chat_id, message_id)
                            r = 'You want me to keep an eye on your {}? I will let you know if it rises or drops to {}'.format(
                                pair, target_price
                            )
                            logging.info(r)
                        except IndexError:
                            r = 'Tell me what price you want an alert for, doofus!'
                else:
                    r = '*KRAKEN:{}* \n*Price:* {} \n*---* \n*High:* {} \n*Low:* {}'.format(pair, price, highPrice, lowPrice)
                # r += '\n\n_updated: {}_'.format(time)
                reply(r)

            elif text.split(' ')[0][1:].upper() in BITT_ASSETPAIRS:
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
                        l_one = highPrice
                        l_two = highPrice - ((highPrice - lowPrice) * 0.236)
                        l_three = highPrice - ((highPrice - lowPrice) * 0.382)
                        l_four = highPrice - ((highPrice - lowPrice) * 0.5)
                        l_five = highPrice - ((highPrice - lowPrice) * 0.618)
                        l_six = highPrice - ((highPrice - lowPrice) * 0.786)
                        l_seven = lowPrice
                        l_eight = highPrice - ((highPrice - lowPrice) * 1.272)
                        l_nine = highPrice - ((highPrice - lowPrice) * 1.618)

                        r = '*BITTREX:{0}* 24h fib levels\n\n*0%*: {1}\n*23.6%*: {2}\n*38.2%*: {3}\n*50%*: {4}\n*61.8%*: {5}\n*78.6%*: {6}\n*100%*: {7}\n\n*127.2%*: {8}\n*161.8%*: {9}\n'.format(pair, l_one, l_two, l_three, l_four, l_five, l_six, l_seven, l_eight, l_nine)

                else:
                    r = '*BITTREX:{}* \n*Price:* {} \n*---* \n*High:* {} \n*Low:* {}'.format(pair, price, highPrice, lowPrice)
                reply(r)



            elif len(text) == 4 or len(text) == 7:
                reply('This asset(pair) is not recognized. Pick one from the /assets list, stupid.')
            else:
                reply('You know, this sort of behaviour could qualify as sexual harassment.')

        # bot text reply's

        elif 'beach' in text:
            reply('dont forget to bring a towel')
        # elif ('sell' in text or 'dropping' in text or 'dumping' in text) and random.choice([True, False]):
        #     reply('weak hands!')
        # elif 'what time' in text:
        #     reply('look at the corner of your screen!')
        # elif 'moon' in text:
        #     reply('http://www.louwmanexclusive.com/nl/brands/lamborghini/')
        # elif 'bitch' in text:
        #     reply('dont talk to me like that!')
        # elif 'penny' in text:
        #     reply('Dont talk behind my back!')
        else:
            if getEnabled(chat_id):
                reply('I got your message! (but I do not know how to answer)')
            else:
                logging.info('not enabled for chat_id {}'.format(chat_id))



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


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
