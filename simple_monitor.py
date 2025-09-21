#!/usr/bin/env python3
"""
简化实时监控 - 显示关键信息
"""

import sys
import os
import time
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.strategy.btc_monitor import btc_monitor
from src.strategy.doge_signals import doge_signal_generator

def simple_monitor():
    """简化监控显示"""
    print("量化交易实时监控")
    print("=" * 60)

    try:
        cycle = 0
        while cycle < 20:  # 运行20个周期
            current_time = datetime.now().strftime('%H:%M:%S')

            try:
                # 获取价格
                btc_ticker = binance_api.get_24hr_ticker('BTCUSDT')
                doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')

                if btc_ticker and doge_ticker:
                    btc_price = float(btc_ticker['lastPrice'])
                    btc_change = float(btc_ticker['priceChangePercent'])
                    doge_price = float(doge_ticker['lastPrice'])
                    doge_change = float(doge_ticker['priceChangePercent'])

                    print(f"[{current_time}]")
                    print(f"  BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)")
                    print(f"  DOGE: ${doge_price:.6f} ({doge_change:+.2f}%)")

                    # 检查BTC条件
                    btc_conditions = btc_monitor.check_all_conditions()
                    btc_status = "满足" if btc_conditions['valid'] else "不满足"
                    print(f"  BTC条件: {btc_status}")

                    # 检查DOGE信号
                    signals = doge_signal_generator.check_all_signals()
                    if signals:
                        for signal in signals:
                            signal_type = signal.get('type', 'unknown').upper()
                            signal_id = signal.get('signal_id', 0)
                            print(f"  *** {signal_type} SIGNAL {signal_id} ***")
                    else:
                        print(f"  信号: 无")

                    print("-" * 60)

                else:
                    print(f"[{current_time}] 数据获取失败")

            except Exception as e:
                print(f"[{current_time}] 错误: {str(e)}")

            cycle += 1
            if cycle < 20:
                time.sleep(5)  # 5秒间隔

    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    simple_monitor()