from AlgoTrader import *

bot = AlgoTrader()

bot.getMovingAvgs()
bot.getOnBalanceVolumes()
bot.getMarketPrices()

ib.sleep(2)

print(bot.marketPrices)

print("trading by moving averages")
bot.tradeByMovingAverages()

print("trading by on-balance volume")
bot.tradeByVolume()

ib.run()