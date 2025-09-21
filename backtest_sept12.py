#!/usr/bin/env python3
"""
9月12日-9月18日历史数据回测
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.indicators.boll import BOLL
from src.indicators.kdj import KDJ

def main():
    """9月12日-9月18日回测"""
    print("=" * 60)
    print("策略回测 - 9月12日至9月18日")
    print("=" * 60)

    try:
        # 获取历史数据
        print("获取历史数据...")
        btc_4h = binance_api.get_klines('BTCUSDT', '4h', 100)
        btc_1h = binance_api.get_klines('BTCUSDT', '1h', 200)
        doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 200)
        doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 500)
        doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 1000)

        if any(df.empty for df in [btc_4h, btc_1h, doge_1h, doge_15m, doge_1m]):
            print("数据获取失败")
            return

        print(f"数据时间范围:")
        print(f"  BTC 1h: {btc_1h.index[0]} 至 {btc_1h.index[-1]}")
        print(f"  DOGE 1h: {doge_1h.index[0]} 至 {doge_1h.index[-1]}")

        # 设定明确的时间范围
        start_date = datetime(2024, 9, 12)
        end_date = datetime(2024, 9, 18, 23, 59, 59)

        print(f"目标分析期间: {start_date} 至 {end_date}")

        # 过滤数据到目标时间范围
        btc_4h_period = btc_4h[(btc_4h.index >= start_date) & (btc_4h.index <= end_date)]
        btc_1h_period = btc_1h[(btc_1h.index >= start_date) & (btc_1h.index <= end_date)]
        doge_1h_period = doge_1h[(doge_1h.index >= start_date) & (doge_1h.index <= end_date)]
        doge_15m_period = doge_15m[(doge_15m.index >= start_date) & (doge_15m.index <= end_date)]
        doge_1m_period = doge_1m[(doge_1m.index >= start_date) & (doge_1m.index <= end_date)]

        print(f"目标期间可用数据:")
        print(f"  BTC 1h: {len(btc_1h_period)}条")
        print(f"  DOGE: 1h({len(doge_1h_period)}条), 15m({len(doge_15m_period)}条), 1m({len(doge_1m_period)}条)")

        if len(btc_1h_period) == 0:
            print("目标期间没有数据，检查最近可用数据...")
            recent_data = btc_1h.tail(168)  # 最近7天数据
            print(f"最近数据时间范围: {recent_data.index[0]} 至 {recent_data.index[-1]}")

            # 使用最近7天数据作为示例
            btc_4h_period = btc_4h.tail(42)  # 7天的4小时数据
            btc_1h_period = btc_1h.tail(168)  # 7天的1小时数据
            doge_1h_period = doge_1h.tail(168)
            doge_15m_period = doge_15m.tail(672)  # 7天的15分钟数据
            doge_1m_period = doge_1m.tail(1000)  # 最近1000条1分钟数据

            print(f"使用最近数据: 1h({len(btc_1h_period)}条)")

        # 初始化技术指标
        boll = BOLL()
        kdj = KDJ()

        signals = []
        btc_conditions = []

        # 按小时检查信号
        print("\n开始分析...")

        time_points = btc_1h_period.index[24:]  # 从第25个数据点开始，确保有足够历史数据

        check_count = 0
        btc_valid_count = 0

        for current_time in time_points:
            check_count += 1

            if check_count % 10 == 1:
                print(f"检查进度: {check_count}/{len(time_points)} - {current_time}")

            # 获取截至当前时间的历史数据
            btc_1h_hist = btc_1h_period[btc_1h_period.index <= current_time].tail(50)
            btc_4h_hist = btc_4h_period[btc_4h_period.index <= current_time].tail(20)

            if len(btc_1h_hist) < 25 or len(btc_4h_hist) < 10:
                continue

            # 计算BTC 24小时统计
            recent_24h = btc_1h_hist.tail(24)
            if len(recent_24h) >= 20:
                open_price = recent_24h['open'].iloc[0]
                high_price = recent_24h['high'].max()
                low_price = recent_24h['low'].min()
                close_price = recent_24h['close'].iloc[-1]

                volatility = (high_price - low_price) / open_price
                change_percent = (close_price - open_price) / open_price

                # BTC条件检查
                volatility_ok = volatility < 0.03  # 3%
                growth_ok = change_percent > 0.01  # 1%
                condition_24h = volatility_ok or growth_ok

                # KDJ条件
                kdj_4h_values = kdj.get_latest_values(btc_4h_hist)
                kdj_1h_values = kdj.get_latest_values(btc_1h_hist)

                kdj_4h = kdj_4h_values.get('KDJ_MAX', 100)
                kdj_1h = kdj_1h_values.get('KDJ_MAX', 100)

                kdj_4h_ok = kdj_4h < 50  # v3.0阈值
                kdj_1h_ok = kdj_1h < 50  # v3.0阈值
                kdj_condition = kdj_4h_ok and kdj_1h_ok

                # 最终BTC条件
                btc_valid = condition_24h and kdj_condition

                btc_condition = {
                    'time': current_time.strftime('%m-%d %H:%M'),
                    'valid': btc_valid,
                    'volatility': volatility * 100,
                    'change': change_percent * 100,
                    'kdj_4h': kdj_4h,
                    'kdj_1h': kdj_1h,
                    'price': close_price
                }
                btc_conditions.append(btc_condition)

                if btc_valid:
                    btc_valid_count += 1
                    print(f"  {current_time.strftime('%m-%d %H:%M')} BTC条件满足！检查DOGE信号...")

                    # 检查DOGE信号
                    doge_1h_hist = doge_1h_period[doge_1h_period.index <= current_time].tail(50)
                    doge_15m_hist = doge_15m_period[doge_15m_period.index <= current_time].tail(100)
                    doge_1m_hist = doge_1m_period[doge_1m_period.index <= current_time].tail(200)

                    if len(doge_1h_hist) >= 25 and len(doge_15m_hist) >= 25 and len(doge_1m_hist) >= 25:
                        # 计算DOGE技术指标
                        boll_1h = boll.get_latest_values(doge_1h_hist)
                        boll_15m = boll.get_latest_values(doge_15m_hist)

                        kdj_1h_doge = kdj.get_latest_values(doge_1h_hist)
                        kdj_15m_doge = kdj.get_latest_values(doge_15m_hist)
                        kdj_1m_doge = kdj.get_latest_values(doge_1m_hist)

                        doge_price = doge_1h_hist['close'].iloc[-1]

                        # 显示当前DOGE技术指标
                        print(f"    DOGE技术指标: 1h布林{boll_1h.get('touch','无')} KDJ{kdj_1h_doge.get('KDJ_MAX',0):.1f}, "
                              f"15m布林{boll_15m.get('touch','无')} KDJ{kdj_15m_doge.get('KDJ_MAX',0):.1f}, "
                              f"1m KDJ{kdj_1m_doge.get('KDJ_MAX',0):.1f}")

                        # 检查买入信号1
                        if (boll_1h.get('touch') == 'DN' and
                            kdj_1h_doge.get('KDJ_MAX', 100) < 10 and
                            boll_15m.get('touch') == 'DN' and
                            kdj_15m_doge.get('KDJ_MAX', 100) < 20 and
                            kdj_1m_doge.get('KDJ_MAX', 100) < 20):

                            signal = {
                                'time': current_time.strftime('%m-%d %H:%M'),
                                'type': 'BUY',
                                'signal_id': 1,
                                'price': doge_price
                            }
                            signals.append(signal)
                            print(f"    *** 买入信号1触发！价格: ${doge_price:.6f}")

                        # 检查买入信号2
                        if (boll_1h.get('touch') == 'MB' and
                            kdj_1h_doge.get('KDJ_MAX', 100) < 15 and
                            boll_15m.get('touch') == 'DN' and
                            kdj_15m_doge.get('KDJ_MAX', 100) < 20 and
                            kdj_1m_doge.get('KDJ_MAX', 100) < 20):

                            signal = {
                                'time': current_time.strftime('%m-%d %H:%M'),
                                'type': 'BUY',
                                'signal_id': 2,
                                'price': doge_price
                            }
                            signals.append(signal)
                            print(f"    *** 买入信号2触发！价格: ${doge_price:.6f}")

                        # 检查买入信号3
                        if (boll_1h.get('touch') == 'MB' and
                            kdj_1h_doge.get('KDJ_MAX', 100) < 15 and
                            boll_15m.get('touch') == 'MB' and
                            kdj_15m_doge.get('KDJ_MAX', 100) < 20 and
                            kdj_1m_doge.get('KDJ_MAX', 100) < 20):

                            signal = {
                                'time': current_time.strftime('%m-%d %H:%M'),
                                'type': 'BUY',
                                'signal_id': 3,
                                'price': doge_price
                            }
                            signals.append(signal)
                            print(f"    *** 买入信号3触发！价格: ${doge_price:.6f}")

        # 生成报告
        print("\n" + "=" * 60)
        print("回测报告 - 9月12日至9月18日")
        print("=" * 60)

        buy_signals = [s for s in signals if s['type'] == 'BUY']

        print(f"检查时间点: {check_count}个")
        print(f"BTC条件满足: {btc_valid_count}次 ({btc_valid_count/check_count*100:.1f}%)")
        print(f"买入信号: {len(buy_signals)}个")

        if buy_signals:
            print(f"\n买入信号详情:")
            for signal in buy_signals:
                print(f"  {signal['time']} - 买入信号{signal['signal_id']}: ${signal['price']:.6f}")
        else:
            print(f"\n期间内未发现买入信号")

        # BTC条件统计
        if btc_conditions:
            avg_volatility = sum(c['volatility'] for c in btc_conditions) / len(btc_conditions)
            avg_change = sum(c['change'] for c in btc_conditions) / len(btc_conditions)
            avg_kdj_4h = sum(c['kdj_4h'] for c in btc_conditions) / len(btc_conditions)
            avg_kdj_1h = sum(c['kdj_1h'] for c in btc_conditions) / len(btc_conditions)

            print(f"\nBTC条件统计:")
            print(f"  平均振幅: {avg_volatility:.2f}%")
            print(f"  平均涨跌: {avg_change:.2f}%")
            print(f"  平均4h KDJ: {avg_kdj_4h:.1f}")
            print(f"  平均1h KDJ: {avg_kdj_1h:.1f}")

        print(f"\n回测完成！")

    except Exception as e:
        print(f"回测失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()