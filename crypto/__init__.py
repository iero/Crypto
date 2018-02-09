from crypto import utils
from crypto import assets
from crypto import market
from crypto import trades
from crypto import portfolio
from crypto import calls
from crypto import klines

# Import exchange clients
from binance.client import Client as binanceClient
from kucoin.client import Client as kucoinClient
# from poloniex import Poloniex as poloClient
from polo import Poloniex as poloClient
from gdax import AuthenticatedClient as gdaxClient
from gdax import PublicClient as gdaxPClient
from bitfinex.client import Client as bitfinexClient
from krakenex import API as krakenClient
