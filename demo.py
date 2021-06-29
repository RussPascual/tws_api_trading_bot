from ib_insync import *
import pandas as pd

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Contract(conId=270639)
# Stock('AMD', 'SMART', 'USD')
# Stock('INTC', 'SMART', 'USD', primaryExchange='NASDAQ')
# Forex('EURUSD')
# CFD('IBUS30')
# Future('ES', '20180921', 'GLOBEX')
# Option('SPY', '20170721', 240, 'C', 'SMART')
# Bond(secIdType='ISIN', secId='US03076KAA60')

# request historical data
stock = Stock('AMD', 'SMART', 'USD')
bars = ib.reqHistoricalData(stock, endDateTime='', durationStr='30 D', barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True)

print(bars)
# tickers
marketData = ib.reqMktData(stock, '', False, False)


def onPendingTicker(ticker):
    print("pending ticker event received")
    print(ticker)


ib.pendingTickersEvent += onPendingTicker


# limit/market orders

# stock = Stock('AMD', 'SMART', 'USD')
limit_order = LimitOrder('BUY', 5, 69)
market_order = MarketOrder('BUY', 5)

limit_trade = ib.placeOrder(stock, limit_order)
market_trade = ib.placeOrder(stock, market_order)

def orderFilled(order, fill):
    print("order has been filled")
    print(order)
    print(fill)


limit_trade.fillEvent += orderFilled
market_trade.fillEvent += orderFilled

# trade history
for trade in ib.trades():
    print('== this is one of my trades')
    print(trade)

for order in ib.orders():
    print('== this is one of my orders')
    print(order)


# options
ib.qualifyContracts(stock)
ib.sleep(1)
chains = ib.reqSecDefOptParams(stock.symbol, '', stock.secType, stock.conId)

print(util.df(chains))

# scanners
subscription = ScannerSubscription(instrument='STK', locationCode='STK.US.MAJOR', scanCode='TOP_PERC_GAIN')

scanData = ib.reqScannerData(subscription)

for scan in scanData:
    print(scan)
    print(scan.contractDetails.contract.symbol)


ib.run()
