from ib_insync import *
import pandas as pd
import time

# connect
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# contracts to trade
TSLA = Stock('TSLA', 'SMART', 'CAD')
AMZN = Stock('AMZN', 'SMART', 'CAD')
MSFT = Stock('MSFT', 'SMART', 'CAD')
AMD = Stock('AMD', 'SMART', 'CAD')

# setup
retryInterval = 60
orderQuantity = 25
marketPrices = {}
movingAvgs = {}
contracts = [TSLA, AMD, MSFT, AMZN]
for c in contracts:
    ib.qualifyContracts(c)


# functions
def orderFilled(order, fill):
    print("order has been filled")
    print(order)
    print(fill)

def onDataReceived(ticker):
    for t in ticker:
        # print(t.contract.symbol, t.ask)
        print(t.contract.symbol, "asking: $", t.ask)
        print(t.contract.symbol, ": 50sma =", movingAvgs[t.contract.symbol][0], ", 200sma =", movingAvgs[t.contract.symbol][1])
        sma50 = movingAvgs[t.contract.symbol][0]
        sma200 = movingAvgs[t.contract.symbol][1]

        # check if should buy
        if (t.ask > sma50 and t.ask > sma200):
            print("Buying", t.contract.symbol)
            order = LimitOrder('BUY', orderQuantity, t.ask)
            limitOrder = ib.placeOrder(t.contract, order)
            limitOrder.fillEvent += orderFilled

        # check if should sell
        elif (t.ask < sma50 and t.ask < sma200):
            print("Selling", t.contract.symbol)
            order = LimitOrder('SELL', orderQuantity, t.ask)
            limitOrder = ib.placeOrder(t.contract, order)
            limitOrder.fillEvent += orderFilled

        else:
            print("No action required")


# check if print in here works

def getMovingAverage(df, days):
    return df[(200 - days):200]["close"].mean()


def calcMovingAvgs():
    global movingAvgs
    global contracts
    for contract in contracts:
        historicalData = ib.reqHistoricalData(contract, endDateTime='', durationStr='200 D', barSizeSetting='1 day',
                                              whatToShow='MIDPOINT', useRTH=True)
        df = util.df(historicalData)

        sma50 = getMovingAverage(df, 50)
        sma200 = getMovingAverage(df, 200)

        movingAvgs[contract.symbol] = [sma50, sma200]


def getMarketPrices():
    global marketPrices
    global contracts
    for contract in contracts:
        ib.reqMktData(contract, '', True, False)
        ib.pendingTickersEvent += onDataReceived


calcMovingAvgs()
while True:
    getMarketPrices()
    ib.sleep(retryInterval)

ib.run()
