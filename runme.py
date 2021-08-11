from AlgoTrader import *

bot = AlgoTrader()

bot.getMovingAvgs()
bot.getMarketPrices()

ib.sleep(2)

print(bot.marketPrices)
bot.tradeByMovingAverages()

ib.run()