#!/usr/bin/env python3
"""
DOGE详细数据监控 - 显示DOGE所有技术指标和买卖信号判断
"""

import sys
import os
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.indicators.boll import BOLL
from src.indicators.kdj import KDJ
from src.strategy.btc_monitor import btc_monitor
from src.strategy.doge_signals import doge_signal_generator

def show_doge_detail():
    """显示DOGE详细分析"""
    print("=" * 100)
    print(f"DOGE/USDT 详细技术分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    try:
        # 1. DOGE基础价格信息
        print("\n[1] DOGE/USDT 价格信息:")
        print("-" * 50)

        doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')
        if doge_ticker:
            current_price = float(doge_ticker['lastPrice'])
            high_24h = float(doge_ticker['highPrice'])
            low_24h = float(doge_ticker['lowPrice'])
            open_24h = float(doge_ticker['openPrice'])
            change_24h = float(doge_ticker['priceChangePercent'])
            volume_24h = float(doge_ticker['volume'])

            print(f"   当前价格: ${current_price:.6f}")
            print(f"   24h开盘价: ${open_24h:.6f}")
            print(f"   24h最高价: ${high_24h:.6f}")
            print(f"   24h最低价: ${low_24h:.6f}")
            print(f"   24h涨跌幅: {change_24h:+.2f}%")
            print(f"   24h成交量: {volume_24h:,.0f} DOGE")

        # 2. 1小时技术指标详细分析
        print("\n[2] 1小时技术指标分析:")
        print("-" * 50)

        doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 50)
        boll = BOLL()
        kdj = KDJ()

        if not doge_1h.empty:
            # BOLL指标详细
            boll_1h = boll.get_latest_values(doge_1h)
            up_1h = boll_1h.get('UP', 0)
            mb_1h = boll_1h.get('MB', 0)
            dn_1h = boll_1h.get('DN', 0)
            close_1h = boll_1h.get('close', 0)
            touch_1h = boll_1h.get('touch', '')

            print(f"   BOLL布林带指标 (20,2):")
            print(f"   - 上轨 UP: ${up_1h:.6f}")
            print(f"   - 中轨 MB: ${mb_1h:.6f}")
            print(f"   - 下轨 DN: ${dn_1h:.6f}")
            print(f"   - 收盘价: ${close_1h:.6f}")
            print(f"   - 触及判断: {touch_1h if touch_1h else '无触及'}")

            # 详细触及条件检查
            print(f"\n   触及条件详细检查:")
            if close_1h >= up_1h:
                print(f"   - 触及上轨: {close_1h:.6f} >= {up_1h:.6f} = True")
            elif close_1h <= dn_1h:
                print(f"   - 触及下轨: {close_1h:.6f} <= {dn_1h:.6f} = True")
            else:
                tolerance = mb_1h * 0.001
                diff = abs(close_1h - mb_1h)
                if diff <= tolerance:
                    print(f"   - 接近中轨: |{close_1h:.6f} - {mb_1h:.6f}| = {diff:.6f} <= {tolerance:.6f} = True")
                else:
                    print(f"   - 距离上轨: {up_1h - close_1h:.6f}")
                    print(f"   - 距离中轨: {abs(close_1h - mb_1h):.6f}")
                    print(f"   - 距离下轨: {close_1h - dn_1h:.6f}")

            # KDJ指标详细
            kdj_1h = kdj.get_latest_values(doge_1h)
            k_1h = kdj_1h.get('K', 0)
            d_1h = kdj_1h.get('D', 0)
            j_1h = kdj_1h.get('J', 0)
            max_1h = kdj_1h.get('KDJ_MAX', 0)

            print(f"\n   KDJ随机指标 (9,3,3):")
            print(f"   - K值: {k_1h:.2f}")
            print(f"   - D值: {d_1h:.2f}")
            print(f"   - J值: {j_1h:.2f}")
            print(f"   - 判断值 MAX(K,D,J): {max_1h:.2f}")

            # KDJ信号判断
            if max_1h < 10:
                print(f"   - 超卖信号: {max_1h:.2f} < 10 = 强超卖")
            elif max_1h < 20:
                print(f"   - 偏超卖: {max_1h:.2f} < 20 = 轻度超卖")
            elif max_1h > 90:
                print(f"   - 超买信号: {max_1h:.2f} > 90 = 超买")
            else:
                print(f"   - 中性区域: 20 <= {max_1h:.2f} <= 90")

        # 3. 15分钟技术指标分析
        print("\n[3] 15分钟技术指标分析:")
        print("-" * 50)

        doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 50)

        if not doge_15m.empty:
            # BOLL指标
            boll_15m = boll.get_latest_values(doge_15m)
            up_15m = boll_15m.get('UP', 0)
            mb_15m = boll_15m.get('MB', 0)
            dn_15m = boll_15m.get('DN', 0)
            close_15m = boll_15m.get('close', 0)
            touch_15m = boll_15m.get('touch', '')

            print(f"   BOLL布林带指标:")
            print(f"   - 上轨 UP: ${up_15m:.6f}")
            print(f"   - 中轨 MB: ${mb_15m:.6f}")
            print(f"   - 下轨 DN: ${dn_15m:.6f}")
            print(f"   - 收盘价: ${close_15m:.6f}")
            print(f"   - 触及判断: {touch_15m if touch_15m else '无触及'}")

            # KDJ指标
            kdj_15m = kdj.get_latest_values(doge_15m)
            max_15m = kdj_15m.get('KDJ_MAX', 0)

            print(f"\n   KDJ随机指标:")
            print(f"   - 判断值: {max_15m:.2f}")

            if max_15m < 10:
                print(f"   - 状态: {max_15m:.2f} < 10 = 强超卖")
            elif max_15m < 15:
                print(f"   - 状态: {max_15m:.2f} < 15 = 超卖")
            elif max_15m > 90:
                print(f"   - 状态: {max_15m:.2f} > 90 = 超买")
            else:
                print(f"   - 状态: 中性区域")

        # 4. 1分钟技术指标分析
        print("\n[4] 1分钟技术指标分析:")
        print("-" * 50)

        doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 50)

        if not doge_1m.empty:
            kdj_1m = kdj.get_latest_values(doge_1m)
            max_1m = kdj_1m.get('KDJ_MAX', 0)

            print(f"   KDJ随机指标:")
            print(f"   - 判断值: {max_1m:.2f}")

            if max_1m < 10:
                print(f"   - 状态: {max_1m:.2f} < 10 = 强超卖")
            elif max_1m < 20:
                print(f"   - 状态: {max_1m:.2f} < 20 = 超卖")
            elif max_1m > 90:
                print(f"   - 状态: {max_1m:.2f} > 90 = 超买")
            else:
                print(f"   - 状态: 中性区域")

        # 5. 买入信号详细检查
        print("\n[5] 买入信号详细检查:")
        print("-" * 50)

        # 获取BTC条件
        btc_condition = btc_monitor.check_all_conditions()
        btc_ok = btc_condition['valid']

        print(f"   前置条件:")
        print(f"   - BTC监控条件: {'满足' if btc_ok else '不满足'}")

        if btc_ok:
            # 买入信号1检查
            print(f"\n   买入信号1条件检查:")
            if 'touch_1h' in locals() and 'max_1h' in locals():
                cond1_1h_dn = touch_1h == 'DN'
                cond1_1h_kdj = max_1h < 10
                cond1_15m_dn = touch_15m == 'DN' if 'touch_15m' in locals() else False
                cond1_15m_kdj = max_15m < 10 if 'max_15m' in locals() else False
                cond1_1m_kdj = max_1m < 20 if 'max_1m' in locals() else False

                print(f"   - 1h触及DN: {touch_1h} == 'DN' = {'满足' if cond1_1h_dn else '不满足'}")
                print(f"   - 1h KDJ<10: {max_1h:.2f} < 10 = {'满足' if cond1_1h_kdj else '不满足'}")
                print(f"   - 15m触及DN: {touch_15m if 'touch_15m' in locals() else '无'} == 'DN' = {'满足' if cond1_15m_dn else '不满足'}")
                print(f"   - 15m KDJ<10: {max_15m if 'max_15m' in locals() else 0:.2f} < 10 = {'满足' if cond1_15m_kdj else '不满足'}")
                print(f"   - 1m KDJ<20: {max_1m if 'max_1m' in locals() else 0:.2f} < 20 = {'满足' if cond1_1m_kdj else '不满足'}")

                buy1_trigger = cond1_1h_dn and cond1_1h_kdj and cond1_15m_dn and cond1_15m_kdj and cond1_1m_kdj
                print(f"   买入信号1: {'触发' if buy1_trigger else '未触发'}")

            # 买入信号2检查
            print(f"\n   买入信号2条件检查:")
            if 'touch_1h' in locals() and 'max_1h' in locals():
                cond2_1h_mb = touch_1h == 'MB'
                cond2_1h_kdj = max_1h < 15
                cond2_15m_dn = touch_15m == 'DN' if 'touch_15m' in locals() else False
                cond2_15m_kdj = max_15m < 15 if 'max_15m' in locals() else False
                cond2_1m_kdj = max_1m < 10 if 'max_1m' in locals() else False

                print(f"   - 1h触及MB: {touch_1h} == 'MB' = {'满足' if cond2_1h_mb else '不满足'}")
                print(f"   - 1h KDJ<15: {max_1h:.2f} < 15 = {'满足' if cond2_1h_kdj else '不满足'}")
                print(f"   - 15m触及DN: {touch_15m if 'touch_15m' in locals() else '无'} == 'DN' = {'满足' if cond2_15m_dn else '不满足'}")
                print(f"   - 15m KDJ<15: {max_15m if 'max_15m' in locals() else 0:.2f} < 15 = {'满足' if cond2_15m_kdj else '不满足'}")
                print(f"   - 1m KDJ<10: {max_1m if 'max_1m' in locals() else 0:.2f} < 10 = {'满足' if cond2_1m_kdj else '不满足'}")

                buy2_trigger = cond2_1h_mb and cond2_1h_kdj and cond2_15m_dn and cond2_15m_kdj and cond2_1m_kdj
                print(f"   买入信号2: {'触发' if buy2_trigger else '未触发'}")

            # 买入信号3检查
            print(f"\n   买入信号3条件检查:")
            if 'touch_1h' in locals() and 'max_1h' in locals():
                cond3_1h_mb = touch_1h == 'MB'
                cond3_1h_kdj = max_1h < 15
                cond3_15m_mb = touch_15m == 'MB' if 'touch_15m' in locals() else False
                cond3_15m_kdj = max_15m < 15 if 'max_15m' in locals() else False
                cond3_1m_kdj = max_1m < 10 if 'max_1m' in locals() else False

                print(f"   - 1h触及MB: {touch_1h} == 'MB' = {'满足' if cond3_1h_mb else '不满足'}")
                print(f"   - 1h KDJ<15: {max_1h:.2f} < 15 = {'满足' if cond3_1h_kdj else '不满足'}")
                print(f"   - 15m触及MB: {touch_15m if 'touch_15m' in locals() else '无'} == 'MB' = {'满足' if cond3_15m_mb else '不满足'}")
                print(f"   - 15m KDJ<15: {max_15m if 'max_15m' in locals() else 0:.2f} < 15 = {'满足' if cond3_15m_kdj else '不满足'}")
                print(f"   - 1m KDJ<10: {max_1m if 'max_1m' in locals() else 0:.2f} < 10 = {'满足' if cond3_1m_kdj else '不满足'}")

                buy3_trigger = cond3_1h_mb and cond3_1h_kdj and cond3_15m_mb and cond3_15m_kdj and cond3_1m_kdj
                print(f"   买入信号3: {'触发' if buy3_trigger else '未触发'}")

        # 6. 卖出信号检查
        print("\n[6] 卖出信号检查:")
        print("-" * 50)

        if 'touch_1h' in locals() and 'max_1h' in locals():
            # 卖出信号通用条件
            sell_1h_kdj_90 = max_1h > 90
            sell_1m_kdj_90 = max_1m > 90 if 'max_1m' in locals() else False

            print(f"   通用条件:")
            print(f"   - 1h KDJ>90: {max_1h:.2f} > 90 = {'满足' if sell_1h_kdj_90 else '不满足'}")
            print(f"   - 1m KDJ>90: {max_1m if 'max_1m' in locals() else 0:.2f} > 90 = {'满足' if sell_1m_kdj_90 else '不满足'}")

            # 检查各卖出信号
            sell_signals = []

            # 卖出信号1
            if touch_1h == 'UP' and sell_1h_kdj_90 and touch_15m == 'MB' and sell_1m_kdj_90:
                sell_signals.append("卖出信号1")

            # 卖出信号2
            if touch_1h == 'UP' and sell_1h_kdj_90 and touch_15m == 'UP' and sell_1m_kdj_90:
                sell_signals.append("卖出信号2")

            # 卖出信号3
            if touch_1h == 'MB' and sell_1h_kdj_90 and touch_15m == 'MB' and sell_1m_kdj_90:
                sell_signals.append("卖出信号3")

            # 卖出信号4
            if touch_1h == 'MB' and sell_1h_kdj_90 and touch_15m == 'UP' and sell_1m_kdj_90:
                sell_signals.append("卖出信号4")

            if sell_signals:
                print(f"   触发的卖出信号: {', '.join(sell_signals)}")
            else:
                print(f"   无卖出信号触发")

        # 7. 系统实际检查结果
        print("\n[7] 系统实际检查结果:")
        print("-" * 50)

        signals = doge_signal_generator.check_all_signals()
        if signals:
            for signal in signals:
                signal_type = signal.get('type', 'unknown').upper()
                signal_id = signal.get('signal_id', 0)
                print(f"   {signal_type} Signal {signal_id}: DOGEUSDT")
        else:
            print(f"   当前无信号触发")

        print("\n" + "=" * 100)

    except Exception as e:
        print(f"数据获取失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_doge_detail()