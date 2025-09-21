#!/usr/bin/env python3
"""
详细监控模式 - 显示具体数值
"""

import sys
import os
import time
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.indicators.boll import BOLL
from src.indicators.kdj import KDJ
from src.strategy.btc_monitor import btc_monitor
from src.strategy.doge_signals import doge_signal_generator
from src.utils.config import config

def show_detailed_status():
    """显示详细的市场状态"""
    print("=" * 80)
    print(f"📊 实时监控数据 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        # 获取BTC数据
        print("\n🟡 BTC/USDT 分析:")
        btc_24h = binance_api.calculate_24h_stats('BTCUSDT')
        btc_ticker = binance_api.get_24hr_ticker('BTCUSDT')

        if btc_ticker:
            print(f"   当前价格: ${btc_ticker['lastPrice']:,.2f}")
            print(f"   24h涨跌: {btc_ticker['priceChangePercent']:+.2f}%")
            print(f"   24h振幅: {btc_24h.get('volatility', 0)*100:.2f}%")
            print(f"   24h成交量: {float(btc_ticker['volume']):,.0f} BTC")

        # BTC KDJ数据
        btc_4h = binance_api.get_klines('BTCUSDT', '4h', 50)
        btc_1h = binance_api.get_klines('BTCUSDT', '1h', 50)

        kdj = KDJ()
        if not btc_4h.empty:
            kdj_4h = kdj.get_latest_values(btc_4h)
            print(f"   4h KDJ: K={kdj_4h.get('K', 0):.1f}, D={kdj_4h.get('D', 0):.1f}, J={kdj_4h.get('J', 0):.1f}")

        if not btc_1h.empty:
            kdj_1h = kdj.get_latest_values(btc_1h)
            print(f"   1h KDJ: K={kdj_1h.get('K', 0):.1f}, D={kdj_1h.get('D', 0):.1f}, J={kdj_1h.get('J', 0):.1f}")

        # 获取DOGE数据
        print("\n🐕 DOGE/USDT 分析:")
        doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')

        if doge_ticker:
            print(f"   当前价格: ${doge_ticker['lastPrice']}")
            print(f"   24h涨跌: {doge_ticker['priceChangePercent']:+.2f}%")
            print(f"   24h成交量: {float(doge_ticker['volume']):,.0f} DOGE")

        # DOGE技术指标
        doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 50)
        doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 50)
        doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 50)

        boll = BOLL()

        if not doge_1h.empty:
            boll_1h = boll.get_latest_values(doge_1h)
            kdj_1h = kdj.get_latest_values(doge_1h)
            print(f"   1h BOLL: UP={boll_1h.get('UP', 0):.6f}, MB={boll_1h.get('MB', 0):.6f}, DN={boll_1h.get('DN', 0):.6f}")
            print(f"   1h 触及: {boll_1h.get('touch', '无')}")
            print(f"   1h KDJ: {kdj_1h.get('KDJ_MAX', 0):.1f}")

        if not doge_15m.empty:
            boll_15m = boll.get_latest_values(doge_15m)
            kdj_15m = kdj.get_latest_values(doge_15m)
            print(f"   15m BOLL: UP={boll_15m.get('UP', 0):.6f}, MB={boll_15m.get('MB', 0):.6f}, DN={boll_15m.get('DN', 0):.6f}")
            print(f"   15m 触及: {boll_15m.get('touch', '无')}")
            print(f"   15m KDJ: {kdj_15m.get('KDJ_MAX', 0):.1f}")

        if not doge_1m.empty:
            kdj_1m = kdj.get_latest_values(doge_1m)
            print(f"   1m KDJ: {kdj_1m.get('KDJ_MAX', 0):.1f}")

        # 检查信号
        print("\n🎯 信号检查:")
        signals = doge_signal_generator.check_all_signals()

        if signals:
            for signal in signals:
                signal_type = signal.get('type', 'unknown').upper()
                signal_id = signal.get('signal_id', 0)
                print(f"   ⚡ {signal_type} Signal {signal_id} - DOGEUSDT")
        else:
            print("   ⭕ 当前无信号触发")

        # BTC条件状态
        btc_status = btc_monitor.get_status_summary()
        print(f"\n📈 BTC策略状态: {btc_status}")

    except Exception as e:
        print(f"❌ 数据获取失败: {str(e)}")

def main():
    """主函数"""
    print("🚀 币安量化交易详细监控")
    print("按 Ctrl+C 退出监控")

    try:
        while True:
            show_detailed_status()
            print(f"\n⏰ 下次更新: 30秒后...")
            print("=" * 80)
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n👋 监控已停止")

if __name__ == "__main__":
    main()