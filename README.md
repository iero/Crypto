# Crypto

Python code for cryptocurrencies (coins and altcoins) manipulation.

Can connect to several services (exchanges platforms) for building your own tools.

## General

Install dependancies :
`pip install --user -r requirements.txt`

For setting a specific conda environnment :
```
conda create -n python3 python=3.6 anaconda
source activate python3
```

Copy ```example.xml``` file somewhere (DO NOT KEEP IN THE SAME DIRECTORY) and rename it to something else. You will use this file using `--params file.xml`. Update params file with sections that apply :
- binance (working)
- kucoin (still need some tests)
- poloniex (in progress but some problems with the lib)
- gdax (in progress)

### Binance

Binance is one of the best trading platform. If you don't have an account yet, please use my [referral link](https://www.binance.com/?ref=18697575). Next, generate API key & secret using [Binance API tool](https://www.binance.com/userCenter/createApi.html), and update the parameters file.
This code uses [python-binance Sammchardy SDK](https://github.com/sammchardy/python-binance) documented [here](https://python-binance.readthedocs.io/en/latest/)

[Binance fees are listed here](https://www.binance.com/fees.html)

### KuCoin (In progress)

Another well known platform with a lot of coins.
After creating an account, generate API key & secret using [KuCoin API tool](https://www.kucoin.com/#/user/setting/api) and update the parameters file. We use [python-kucoin Sammchardy SDK](https://github.com/sammchardy/python-kucoin) documented [here](https://python-kucoin.readthedocs.io).

[Kucoin fees are listed here](https://news.kucoin.com/en/fee/)

### Poloniex (In progress)

Generate API key & secret on [Poloniex API tool](https://poloniex.com/apiKeys) and update parameters file
We use [poloniex Aula13 SDK](https://github.com/Aula13/poloniex) and [official Poloniex API documentation is here (https://poloniex.com/support/api/)

### GDAX

This code use [GDAX danpaquin SDK](https://github.com/danpaquin/gdax-python)

### Kraken (in progress)

[Official Kraken API documentation](https://www.kraken.com/help/api#public-market-data)

## Portfolio

Show a status of your finance portfolio in real-time, with pending transactions

- Launch : `python portfolio_watch.py --params ../crypto.xml`
To see dust assets (< 5 usd), use `--dust`

```
    ---------- Portfolio ----
          quantity       eth       btc     usd Percent
    BNB      0.869  0.012123  0.001111   12.64      2%
    BTC      0.016  0.172864  0.015832  180.25     22%
    ...

    ---------- Active Trades ----
           quantity    target     price  side   type
    symbol
    OMGBTC    2.500  0.001915  0.001613  SELL  LIMIT
    ...

```

## Market watch

Record Binance real time market price in a csv file for further analysis

- Update output line in your conf file
- Launch : `python market_watch.py --params ../crypto.xml --loop 10`
- File is updated every 10sec

# Market history (works with binance, kucoin and poloniex)

Record 5 minutes candles for further analysis (and model training)
On first launch, save historical data since exchange opening
If relaunch, it updates file since last record

- Launch : `python get_historical_klines.py --params ../crypto.xml`

Can launch with a special pair (exchange dependant) `--pair ETHBTC` or on a given exchange `--exchange binance`.

```
$ head -n 3 crypto/history/binance/history_BNBBTC.csv
time,Open,High,Low,Close,Volume
2017-07-14 04:00:00,5e-05,5.3e-05,1e-05,3.615e-05,1469912.0
2017-07-14 04:05:00,3.9e-05,4e-05,3.655e-05,4e-05,1031546.0
```

Be carefull, it can be heavy
```
du -hs crypto/history/*
376M    crypto/history/binance
119M    crypto/history/kucoin
734M    crypto/history/poloniex/
``
