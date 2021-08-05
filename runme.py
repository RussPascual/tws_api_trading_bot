from AlgoTrader import AlgoTrader
import time

bot = AlgoTrader()
print(bot.contracts)

bot.getMovingAvgs()
time.sleep(2)
print(bot.movingAverages)