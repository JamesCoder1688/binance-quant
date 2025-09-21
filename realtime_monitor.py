#!/usr/bin/env python3
"""
实时监控 - 显示5秒间隔的价格变化
"""

import sys
import os
import time
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api

def realtime_price_monitor():
    """实时价格监控"""
    print("实时价格监控 - 5秒间隔")
    print("=" * 80)
    print("时间         | BTC价格    | 变化     | DOGE价格   | 变化     ")
    print("-" * 80)

    last_btc_price = None
    last_doge_price = None

    try:
        cycle = 0
        while cycle < 10:  # 运行10个周期 (50秒)
            current_time = datetime.now().strftime('%H:%M:%S')

            # 获取价格
            btc_ticker = binance_api.get_24hr_ticker('BTCUSDT')
            doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')

            if btc_ticker and doge_ticker:
                btc_price = float(btc_ticker['lastPrice'])
                doge_price = float(doge_ticker['lastPrice'])

                # 计算变化
                btc_change = ""
                doge_change = ""

                if last_btc_price is not None:
                    btc_diff = btc_price - last_btc_price
                    if btc_diff > 0:
                        btc_change = f"+${btc_diff:.2f}"
                    elif btc_diff < 0:
                        btc_change = f"-${abs(btc_diff):.2f}"
                    else:
                        btc_change = "0.00"

                if last_doge_price is not None:
                    doge_diff = doge_price - last_doge_price
                    if doge_diff > 0:
                        doge_change = f"+${doge_diff:.6f}"
                    elif doge_diff < 0:
                        doge_change = f"-${abs(doge_diff):.6f}"
                    else:
                        doge_change = "0.000000"

                # 输出数据
                print(f"{current_time} | ${btc_price:>9,.2f} | {btc_change:>8} | ${doge_price:>8.6f} | {doge_change:>10}")

                last_btc_price = btc_price
                last_doge_price = doge_price

            cycle += 1
            if cycle < 10:
                time.sleep(5)

    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    realtime_price_monitor()