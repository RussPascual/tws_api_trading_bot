from ib_insync import *
import pandas as pd
import time

# connect
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)


# contracts to trade
TSLA = Stock('TSLA', 'SMART', 'USD')
AMZN = Stock('AMZN', 'SMART', 'USD')
MSFT = Stock('MSFT', 'SMART', 'USD')
AMD = Stock('AMD', 'SMART', 'USD')


# setup
retryInterval = 60
orderQuantity = 25
marketPrices = {}
movingAvgs = {}
contracts = [TSLA, AMD]


# functions
def onDataReceived(ticker):
    print("market data received for ", ticker.contract.symbol + ": asking $" + ticker.ask)
    marketPrices[ticker.contract.symbol] = ticker.ask


def getMovingAverage(df, days):
    return df[(200-days):200]["close"].mean()


def calcMovingAvgs():
    global movingAvgs
    global contracts
    for contract in contracts:
        historicalData = ib.reqHistoricalData(contract, endDateTime='', durationStr='200 D', barSizeSetting='1 day', whatToShow='MIDPOINT', useRTH=True)
        df = util.df(historicalData)

        sma50 = getMovingAverage(df, 50)
        sma200 = getMovingAverage(df, 200)

        movingAvgs[contract.symbol] = [sma50, sma200]


def getMarketPrices():
    global marketPrices
    global contracts
    for contract in contracts:
        ib.reqMktData(contract, '', False, False)
        ib.pendingTickersEvent += onDataReceived


calcMovingAvgs()
getMarketPrices()
print(movingAvgs)
# print(marketPrices)

for contract in contracts:
    # print("market price for ", contract.symbol, ": asking $" + marketPrices[contract.symbol])
    print("50 day moving average for ", contract.symbol, ": " + str(movingAvgs[contract.symbol][0]))
    print("200 day moving average for ", contract.symbol, ": " + str(movingAvgs[contract.symbol][1]))

# get market prices at current time.
# check if market price is above 50sma and 200sma
#   if yes then buy
# check if market price is below 50sma and 200sma
#   if yes then sell

def orderFilled(order, fill):
    print("order has been filled")
    print(order)
    print(fill)

def placeEligibleOrders():
    while True:
        getMarketPrices()

        for contract in contracts:
            marketPrice = marketPrices[contract.symbol]
            sma50 = movingAvgs[contract.symbol][0]
            sma200 = movingAvgs[contract.symbol][1]

            if (marketPrice > sma50 and marketPrice > sma200):
                order = LimitOrder('BUY', orderQuantity, marketPrice)
                limitOrder = ib.placeOrder(contract, order)
                limitOrder.fillEvent += orderFilled

            if (marketPrice < sma50 and marketPrice < sma200):
                order = LimitOrder('SELL', orderQuantity, marketPrice)
                limitOrder = ib.placeOrder(contract, order)
                limitOrder.fillEvent += orderFilled

        time.sleep(retryInterval)
