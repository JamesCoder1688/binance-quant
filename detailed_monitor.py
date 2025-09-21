#!/usr/bin/env python3
"""
详细数据监控 - 显示所有计算过程和具体数值
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

def show_detailed_data():
    """显示详细的数据和计算过程"""
    print("=" * 100)
    print(f"详细监控数据 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    try:
        # 1. BTC/USDT 详细分析
        print("\n[1] BTC/USDT 完整分析:")
        print("-" * 50)

        # 24小时统计
        btc_24h = binance_api.calculate_24h_stats('BTCUSDT')
        btc_ticker = binance_api.get_24hr_ticker('BTCUSDT')

        if btc_ticker:
            current_price = float(btc_ticker['lastPrice'])
            high_24h = float(btc_ticker['highPrice'])
            low_24h = float(btc_ticker['lowPrice'])
            open_24h = float(btc_ticker['openPrice'])
            volume_24h = float(btc_ticker['volume'])
            change_24h = float(btc_ticker['priceChangePercent'])

            print(f"   当前价格: ${current_price:,.2f}")
            print(f"   24h 开盘: ${open_24h:,.2f}")
            print(f"   24h 最高: ${high_24h:,.2f}")
            print(f"   24h 最低: ${low_24h:,.2f}")
            print(f"   24h 成交量: {volume_24h:,.0f} BTC")
            print(f"   24h 涨跌: {change_24h:+.2f}%")

            # 振幅计算详情
            volatility = btc_24h.get('volatility', 0)
            print(f"   振幅计算: ({high_24h:,.2f} - {low_24h:,.2f}) / {open_24h:,.2f} = {volatility:.4f} = {volatility*100:.2f}%")
            print(f"   振幅条件: {volatility*100:.2f}% < 3.0% = {'满足' if volatility < 0.03 else '不满足'}")

            # 涨幅条件
            growth_ok = change_24h/100 > 0.01
            print(f"   涨幅条件: {change_24h:.2f}% > 1.0% = {'满足' if growth_ok else '不满足'}")

            condition_24h = volatility < 0.03 or growth_ok
            print(f"   24h总结: {'满足' if condition_24h else '不满足'} (振幅<3% 或 涨幅>1%)")

        # BTC KDJ分析
        print("\n   KDJ技术指标分析:")

        # 4小时KDJ
        btc_4h = binance_api.get_klines('BTCUSDT', '4h', 50)
        kdj = KDJ()

        if not btc_4h.empty:
            kdj_4h_values = kdj.get_latest_values(btc_4h)
            k_4h = kdj_4h_values.get('K', 0)
            d_4h = kdj_4h_values.get('D', 0)
            j_4h = kdj_4h_values.get('J', 0)
            max_4h = kdj_4h_values.get('KDJ_MAX', 0)

            print(f"   4h KDJ: K={k_4h:.2f}, D={d_4h:.2f}, J={j_4h:.2f}")
            print(f"   4h MAX: max({k_4h:.2f}, {d_4h:.2f}, {j_4h:.2f}) = {max_4h:.2f}")
            print(f"   4h 条件: {max_4h:.2f} < 100 = {'满足' if max_4h < 100 else '不满足'}")

        # 1小时KDJ
        btc_1h = binance_api.get_klines('BTCUSDT', '1h', 50)

        if not btc_1h.empty:
            kdj_1h_values = kdj.get_latest_values(btc_1h)
            k_1h = kdj_1h_values.get('K', 0)
            d_1h = kdj_1h_values.get('D', 0)
            j_1h = kdj_1h_values.get('J', 0)
            max_1h = kdj_1h_values.get('KDJ_MAX', 0)

            print(f"   1h KDJ: K={k_1h:.2f}, D={d_1h:.2f}, J={j_1h:.2f}")
            print(f"   1h MAX: max({k_1h:.2f}, {d_1h:.2f}, {j_1h:.2f}) = {max_1h:.2f}")
            print(f"   1h 条件: {max_1h:.2f} < 100 = {'满足' if max_1h < 100 else '不满足'}")

            kdj_condition = max_4h < 100 and max_1h < 100
            print(f"   KDJ总结: {'满足' if kdj_condition else '不满足'} (4hKDJ<100 且 1hKDJ<100)")

        # BTC总体条件
        btc_all_conditions = btc_monitor.check_all_conditions()
        print(f"\n   BTC策略总结: {'✅ 全部满足' if btc_all_conditions['valid'] else '❌ 不满足'}")

        # 2. DOGE/USDT 详细分析
        print("\n\n[2] DOGE/USDT 完整分析:")
        print("-" * 50)

        # DOGE 24小时数据
        doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')

        if doge_ticker:
            doge_price = float(doge_ticker['lastPrice'])
            doge_change = float(doge_ticker['priceChangePercent'])
            doge_volume = float(doge_ticker['volume'])
            doge_high = float(doge_ticker['highPrice'])
            doge_low = float(doge_ticker['lowPrice'])

            print(f"   当前价格: ${doge_price:.6f}")
            print(f"   24h 最高: ${doge_high:.6f}")
            print(f"   24h 最低: ${doge_low:.6f}")
            print(f"   24h 涨跌: {doge_change:+.2f}%")
            print(f"   24h 成交量: {doge_volume:,.0f} DOGE")

        # DOGE技术指标详细分析
        boll = BOLL()

        # 1小时数据
        print("\n   1小时技术指标:")
        doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 50)

        if not doge_1h.empty:
            # BOLL指标
            boll_1h = boll.get_latest_values(doge_1h)
            up_1h = boll_1h.get('UP', 0)
            mb_1h = boll_1h.get('MB', 0)
            dn_1h = boll_1h.get('DN', 0)
            close_1h = boll_1h.get('close', 0)
            touch_1h = boll_1h.get('touch', '')

            print(f"   BOLL上轨: ${up_1h:.6f}")
            print(f"   BOLL中轨: ${mb_1h:.6f}")
            print(f"   BOLL下轨: ${dn_1h:.6f}")
            print(f"   当前价格: ${close_1h:.6f}")
            print(f"   触及判断: {touch_1h if touch_1h else '无'}")

            # 触及条件详细说明
            if close_1h >= up_1h:
                print(f"   触及上轨: {close_1h:.6f} >= {up_1h:.6f} = True")
            elif close_1h <= dn_1h:
                print(f"   触及下轨: {close_1h:.6f} <= {dn_1h:.6f} = True")
            elif abs(close_1h - mb_1h) <= mb_1h * 0.001:
                print(f"   接近中轨: |{close_1h:.6f} - {mb_1h:.6f}| <= {mb_1h * 0.001:.6f} = True")
            else:
                print(f"   无明显触及")

            # KDJ指标
            kdj_1h = kdj.get_latest_values(doge_1h)
            k_1h_doge = kdj_1h.get('K', 0)
            d_1h_doge = kdj_1h.get('D', 0)
            j_1h_doge = kdj_1h.get('J', 0)
            max_1h_doge = kdj_1h.get('KDJ_MAX', 0)

            print(f"   KDJ: K={k_1h_doge:.2f}, D={d_1h_doge:.2f}, J={j_1h_doge:.2f}")
            print(f"   KDJ_MAX: {max_1h_doge:.2f}")

        # 15分钟数据
        print("\n   15分钟技术指标:")
        doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 50)

        if not doge_15m.empty:
            boll_15m = boll.get_latest_values(doge_15m)
            up_15m = boll_15m.get('UP', 0)
            mb_15m = boll_15m.get('MB', 0)
            dn_15m = boll_15m.get('DN', 0)
            close_15m = boll_15m.get('close', 0)
            touch_15m = boll_15m.get('touch', '')

            print(f"   BOLL上轨: ${up_15m:.6f}")
            print(f"   BOLL中轨: ${mb_15m:.6f}")
            print(f"   BOLL下轨: ${dn_15m:.6f}")
            print(f"   当前价格: ${close_15m:.6f}")
            print(f"   触及判断: {touch_15m if touch_15m else '无'}")

            kdj_15m = kdj.get_latest_values(doge_15m)
            max_15m_doge = kdj_15m.get('KDJ_MAX', 0)
            print(f"   KDJ_MAX: {max_15m_doge:.2f}")

        # 1分钟数据
        print("\n   1分钟技术指标:")
        doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 50)

        if not doge_1m.empty:
            kdj_1m = kdj.get_latest_values(doge_1m)
            max_1m_doge = kdj_1m.get('KDJ_MAX', 0)
            print(f"   KDJ_MAX: {max_1m_doge:.2f}")

        # 3. 买卖信号详细检查
        print("\n\n[3] 买卖信号详细检查:")
        print("-" * 50)

        # 检查买入信号1
        print("\n   买入信号1检查:")
        print(f"   - BTC条件: {'✅' if btc_all_conditions['valid'] else '❌'}")
        if 'doge_1h' in locals() and not doge_1h.empty:
            signal1_cond1 = touch_1h == 'DN'
            signal1_cond2 = max_1h_doge < 10
            signal1_cond3 = touch_15m == 'DN' if 'touch_15m' in locals() else False
            signal1_cond4 = max_15m_doge < 10 if 'max_15m_doge' in locals() else False
            signal1_cond5 = max_1m_doge < 20 if 'max_1m_doge' in locals() else False

            print(f"   - DOGE 1h触及DN: {touch_1h} == 'DN' = {'✅' if signal1_cond1 else '❌'}")
            print(f"   - DOGE 1h KDJ<10: {max_1h_doge:.2f} < 10 = {'✅' if signal1_cond2 else '❌'}")
            print(f"   - DOGE 15m触及DN: {touch_15m if 'touch_15m' in locals() else '无'} == 'DN' = {'✅' if signal1_cond3 else '❌'}")
            print(f"   - DOGE 15m KDJ<10: {max_15m_doge if 'max_15m_doge' in locals() else 0:.2f} < 10 = {'✅' if signal1_cond4 else '❌'}")
            print(f"   - DOGE 1m KDJ<20: {max_1m_doge if 'max_1m_doge' in locals() else 0:.2f} < 20 = {'✅' if signal1_cond5 else '❌'}")

            buy1_trigger = (btc_all_conditions['valid'] and signal1_cond1 and
                           signal1_cond2 and signal1_cond3 and signal1_cond4 and signal1_cond5)
            print(f"   买入信号1: {'🟢 触发' if buy1_trigger else '⭕ 未触发'}")

        # 检查实际信号
        print("\n   实际信号检查结果:")
        signals = doge_signal_generator.check_all_signals()

        if signals:
            for signal in signals:
                signal_type = signal.get('type', 'unknown').upper()
                signal_id = signal.get('signal_id', 0)
                print(f"   🚨 {signal_type} Signal {signal_id}: DOGEUSDT")
        else:
            print("   ⭕ 当前无信号触发")

        print("\n" + "=" * 100)

    except Exception as e:
        print(f"数据获取失败: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主函数 - 运行一次详细检查"""
    print("币安量化交易 - 详细数据监控")
    print("显示所有计算过程和具体数值")

    show_detailed_data()
    print(f"\n运行完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()