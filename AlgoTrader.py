from ib_insync import *
import pandas as pd

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

class AlgoTrader:
    def __init__(self):
        self.contracts = []
        symbols = open('symbols.txt').readlines()

        for s in symbols:
            c = Stock(s.strip().strip('\n'), 'SMART', 'USD')
            ib.qualifyContracts(c)
            self.contracts.append(c)

        self.buyQuantity = 25
        self.sellQuantity = 25
        self.marketPrices = {}
        self.movingAverages = {}
        self.onBalanceVolumes = {}
        self.closingPrices = {}

    def updateContracts(self):
        self.contracts = []
        symbols = open('symbols.txt').readlines()

        for s in symbols:
            c = Stock(s.strip().strip('\n'), 'SMART', 'USD')
            ib.qualifyContracts(c)
            self.contracts.append(c)

    def calcMovingAvgs(self, df, days):
        return df[(200 - days):200]["close"].mean()
    
    def test(self):
        data = ib.reqHistoricalData(self.contracts[0], endDateTime='', durationStr='200 D', barSizeSetting='1 day',
                                                  whatToShow='MIDPOINT', useRTH=True)
        ib.sleep(2)
        print(util.df(data))

    def getMovingAvgs(self):
        for contract in self.contracts:
            historicalData = ib.reqHistoricalData(contract, endDateTime='', durationStr='200 D', barSizeSetting='1 day',
                                                  whatToShow='MIDPOINT', useRTH=True)
            df = util.df(historicalData)
            sma50 = self.calcMovingAvgs(df, 50)
            sma200 = self.calcMovingAvgs(df, 200)

            self.movingAverages[contract.symbol] = [sma50, sma200]
    
    def onDataReceived(self, ticker):
        for t in ticker:
            self.marketPrices[t.contract.symbol] = t.ask

            # print(t.contract.symbol, ":", t.ask)
            # print(self.marketPrices)

    def getMarketPrices(self):
        for contract in self.contracts:
            ib.reqMktData(contract, '', True, False)
            ib.pendingTickersEvent += self.onDataReceived

    def tradeByMovingAverages(self):
        self.updateContracts()
        self.getMarketPrices()
        self.getMovingAvgs()
        ib.sleep(3)

        for contract in self.contracts:
            print(contract.symbol + ":[" + str(self.movingAverages[contract.symbol][0]) + ", " + str(self.movingAverages[contract.symbol][1]), "], asking", self.marketPrices[contract.symbol])

            # buy if market price > 50sma and 200sma
            if self.movingAverages[contract.symbol][0] < self.marketPrices[contract.symbol] and self.movingAverages[contract.symbol][1] < self.marketPrices[contract.symbol]:
                order = LimitOrder('BUY', self.buyQuantity, self.marketPrices[contract.symbol])
                limitOrder = ib.placeOrder(contract, order)
                print("Buying", contract.symbol, "@", self.marketPrices[contract.symbol])

            
            # sell if market price < 50sma and 200sma
            if self.movingAverages[contract.symbol][0] > self.marketPrices[contract.symbol] and self.movingAverages[contract.symbol][1] > self.marketPrices[contract.symbol]:
                order = LimitOrder('SELL', self.sellQuantity, self.marketPrices[contract.symbol])
                limitOrder = ib.placeOrder(contract, order)
                print("Selling", contract.symbol, "@", self.marketPrices[contract.symbol])

    def calcOnBalanceVolumes(self, df, days):
        closingPrices = df["close"]
        volumes = df["volume"]

        obvs = [0]
        day = 1

        while day < days:
            obv = obvs[day - 1]
            if closingPrices[day] > closingPrices[day - 1]:
                obv += volumes[day]
            elif closingPrices[day] < closingPrices[day - 1]:
                obv -= volumes[day]
            obvs.append(obv)
            day += 1

        return obvs

    def getOnBalanceVolumes(self):
        for contract in self.contracts:
            historicalData = ib.reqHistoricalData(contract, endDateTime='', durationStr='120 D', barSizeSetting='1 day',
                                                  whatToShow='TRADES', useRTH=True)
            df = util.df(historicalData)

            self.onBalanceVolumes[contract.symbol] = self.calcOnBalanceVolumes(df, 120)
            self.closingPrices[contract.symbol] = df["close"]


    def tradeByVolume(self): # On-Balance Volume
        self.updateContracts()
        self.getMarketPrices()
        self.getMovingAvgs()
        ib.sleep(3)
        
        for contract in self.contracts:
            obvs = self.onBalanceVolumes[contract.symbol]
            closingPrices = self.closingPrices[contract.symbol]

            resistanceObv = max(obvs[:119])
            supportObv = min(obvs[:119])
            currObv = obvs[119]

            resistancePrice = max(closingPrices[:119])
            supportPrice = min(closingPrices[:119])
            acceptableMargin = (resistancePrice - supportPrice) * 0.1
            currPrice = closingPrices[119]

            print("checking 1st scenario")
            # OBV hits a new high while the price tests resistance: bullish divergence
            if currObv > resistanceObv and currPrice > resistancePrice - acceptableMargin:
                order = LimitOrder('BUY', self.buyQuantity, self.marketPrices[contract.symbol])
                ib.placeOrder(contract, order)
                print("Buying", contract.symbol, "@", self.marketPrices[contract.symbol])

            print("checking 2nd scenario")
            # The price hits a new high while OBV grinds at or below the last resistance level: bearish divergence
            if currPrice > resistancePrice and currObv <= resistanceObv:
                order = LimitOrder('SELL', self.sellQuantity, self.marketPrices[contract.symbol])
                ib.placeOrder(contract, order)
                print("Selling", contract.symbol, "@", self.marketPrices[contract.symbol])

            print("checking 3rd scenario")
            # OBV hits new low while price tests support: bearish divergence
            if currObv < supportObv and currPrice < supportPrice + acceptableMargin:
                order = LimitOrder('SELL', self.sellQuantity, self.marketPrices[contract.symbol])
                ib.placeOrder(contract, order)
                print("Selling", contract.symbol, "@", self.marketPrices[contract.symbol])

            print("checking 4th scenario")
            # The price hits a new low while OBV grinds at or above the last support level: bullish divergence
            if currPrice < supportPrice and currObv >= supportObv:
                order = LimitOrder('BUY', self.buyQuantity, self.marketPrices[contract.symbol])
                ib.placeOrder(contract, order)
                print("Buying", contract.symbol, "@", self.marketPrices[contract.symbol])

            print(resistanceObv, supportObv, currObv)
            print(resistancePrice, supportPrice, acceptableMargin, currPrice)
            # OBV matches the price action, higher or lower: bullish or bearish convergence, depending on direction.
