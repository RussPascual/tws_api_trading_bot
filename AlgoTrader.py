from ib_insync import *
import pandas as pd

TSLA = Stock('TSLA', 'SMART', 'CAD')
AMZN = Stock('AMZN', 'SMART', 'CAD')
MSFT = Stock('MSFT', 'SMART', 'CAD')
AMD = Stock('AMD', 'SMART', 'CAD')

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

class AlgoTrader:
    def __init__(self):
        self.contracts = [TSLA, AMZN, MSFT, AMD]
        for c in self.contracts:
            self.ib.qualifyContracts(c)
        self.buyQuantity = 25
        self.sellQuanitity = 25
        self.marketPrices = {}
        self.movingAverages = {}
    
    def calcMovingAvgs(self, df, days):
        return df[(200 - days):200]["close"].mean()

    def getMovingAvgs(self):
        for contract in self.contracts:
            historicalData = ib.reqHistoricalData(contract, endDateTime='', durationStr='200 D', barSizeSetting='1 day',
                                              whatToShow='MIDPOINT', useRTH=True)
            df = util.df(historicalData)
            sma50 = ib.getMovingAverage(df, 50)
            sma200 = ib.getMovingAverage(df, 200)

            ib.movingAvgs[contract.symbol] = [sma50, sma200]
    
    def onDataReceived(self, ticker):
        for t in ticker:
            self.marketPrices[t.contract.symbol] = t.ask

    def getMarketPrices(self):
        for contract in self.contracts:
            ib.reqMktData(contract, '', True, False)
            ib.pendingTickersEvent += self.onDataReceived

    def orderFilled(self, order, fill):
        print("order has been filled")
        print(order)
        print(fill)

    def tradeByMovingAverages(self):
        for contract in self.contracts:

            # buy if market price > 50sma and 200sma
            if self.movingAverages[contract.symbol][0] > self.marketPrices[contract.symbol] and self.movingAverages[contract.symbol][1] > self.marketPrices[contract.symbol]:
                order = LimitOrder('BUY', self.orderQuantity, self.marketPrices[contract.symbol])
                limitOrder = ib.placeOrder('BUY', self.buyQuantity, self.marketPrices[contract.symbol])
                limitOrder.fillEvent += self.orderFilled
            
            # sell if market price < 50sma and 200sma
            if self.movingAverages[contract.symbol][0] < self.marketPrices[contract.symbol] and self.movingAverages[contract.symbol][1] < self.marketPrices[contract.symbol]:
                order = LimitOrder('SELL', self.orderQuantity, self.marketPrices[contract.symbol])
                limitOrder = ib.placeOrder('SELL', self.buyQuantity, self.marketPrices[contract.symbol])
                limitOrder.fillEvent += self.orderFilled


