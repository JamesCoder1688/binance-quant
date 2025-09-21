#!/usr/bin/env python3
"""
超详细检查9月17日的买卖点
使用5分钟和1分钟间隔检查，确保不漏掉任何信号
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

def check_btc_conditions(btc_1h_data, btc_4h_data, kdj, current_time):
    """检查BTC条件"""
    try:
        # 获取当前时间前的数据
        btc_1h_recent = btc_1h_data[btc_1h_data.index <= current_time].tail(50)
        btc_4h_recent = btc_4h_data[btc_4h_data.index <= current_time].tail(20)

        if len(btc_1h_recent) < 25 or len(btc_4h_recent) < 10:
            return None

        # 计算24小时统计
        recent_24h = btc_1h_recent.tail(24)
        if len(recent_24h) < 20:
            return None

        open_price = recent_24h['open'].iloc[0]
        high_price = recent_24h['high'].max()
        low_price = recent_24h['low'].min()
        close_price = recent_24h['close'].iloc[-1]

        volatility = (high_price - low_price) / open_price
        change_percent = (close_price - open_price) / open_price

        # 24小时条件
        volatility_ok = volatility < 0.03  # 3%
        growth_ok = change_percent > 0.01  # 1%
        condition_24h = volatility_ok or growth_ok

        # KDJ条件
        kdj_4h_values = kdj.get_latest_values(btc_4h_recent)
        kdj_1h_values = kdj.get_latest_values(btc_1h_recent)

        kdj_4h = kdj_4h_values.get('KDJ_MAX', 100)
        kdj_1h = kdj_1h_values.get('KDJ_MAX', 100)

        kdj_4h_ok = kdj_4h < 50  # v3.0阈值
        kdj_1h_ok = kdj_1h < 50  # v3.0阈值
        kdj_condition = kdj_4h_ok and kdj_1h_ok

        # 最终条件
        btc_valid = condition_24h and kdj_condition

        return {
            'valid': btc_valid,
            'volatility': volatility * 100,
            'change': change_percent * 100,
            'kdj_4h': kdj_4h,
            'kdj_1h': kdj_1h,
            'price': close_price,
            'volatility_ok': volatility_ok,
            'growth_ok': growth_ok,
            'condition_24h': condition_24h,
            'kdj_condition': kdj_condition
        }

    except Exception as e:
        return None

def check_doge_signals(doge_1h_data, doge_15m_data, doge_1m_data, boll, kdj, current_time):
    """检查DOGE信号"""
    try:
        # 获取当前时间前的数据
        doge_1h_recent = doge_1h_data[doge_1h_data.index <= current_time].tail(50)
        doge_15m_recent = doge_15m_data[doge_15m_data.index <= current_time].tail(100)
        doge_1m_recent = doge_1m_data[doge_1m_data.index <= current_time].tail(200)

        if len(doge_1h_recent) < 25 or len(doge_15m_recent) < 25 or len(doge_1m_recent) < 25:
            return [], {}

        # 计算技术指标
        boll_1h = boll.get_latest_values(doge_1h_recent)
        boll_15m = boll.get_latest_values(doge_15m_recent)

        kdj_1h_doge = kdj.get_latest_values(doge_1h_recent)
        kdj_15m_doge = kdj.get_latest_values(doge_15m_recent)
        kdj_1m_doge = kdj.get_latest_values(doge_1m_recent)

        doge_price = doge_1h_recent['close'].iloc[-1]

        signals = []

        # 获取指标值
        boll_1h_touch = boll_1h.get('touch', '')
        boll_15m_touch = boll_15m.get('touch', '')
        kdj_1h_val = kdj_1h_doge.get('KDJ_MAX', 100)
        kdj_15m_val = kdj_15m_doge.get('KDJ_MAX', 100)
        kdj_1m_val = kdj_1m_doge.get('KDJ_MAX', 100)

        # 买入信号1
        signal1_conditions = {
            '1h_boll_dn': boll_1h_touch == 'DN',
            '1h_kdj_10': kdj_1h_val < 10,
            '15m_boll_dn': boll_15m_touch == 'DN',
            '15m_kdj_20': kdj_15m_val < 20,
            '1m_kdj_20': kdj_1m_val < 20
        }

        if all(signal1_conditions.values()):
            signals.append({
                'type': 'BUY',
                'signal_id': 1,
                'price': doge_price,
                'conditions': signal1_conditions,
                'indicators': {
                    '1h_boll': boll_1h_touch,
                    '15m_boll': boll_15m_touch,
                    '1h_kdj': kdj_1h_val,
                    '15m_kdj': kdj_15m_val,
                    '1m_kdj': kdj_1m_val
                }
            })

        # 买入信号2
        signal2_conditions = {
            '1h_boll_mb': boll_1h_touch == 'MB',
            '1h_kdj_15': kdj_1h_val < 15,
            '15m_boll_dn': boll_15m_touch == 'DN',
            '15m_kdj_20': kdj_15m_val < 20,
            '1m_kdj_20': kdj_1m_val < 20
        }

        if all(signal2_conditions.values()):
            signals.append({
                'type': 'BUY',
                'signal_id': 2,
                'price': doge_price,
                'conditions': signal2_conditions,
                'indicators': {
                    '1h_boll': boll_1h_touch,
                    '15m_boll': boll_15m_touch,
                    '1h_kdj': kdj_1h_val,
                    '15m_kdj': kdj_15m_val,
                    '1m_kdj': kdj_1m_val
                }
            })

        # 买入信号3
        signal3_conditions = {
            '1h_boll_mb': boll_1h_touch == 'MB',
            '1h_kdj_15': kdj_1h_val < 15,
            '15m_boll_mb': boll_15m_touch == 'MB',
            '15m_kdj_20': kdj_15m_val < 20,
            '1m_kdj_20': kdj_1m_val < 20
        }

        if all(signal3_conditions.values()):
            signals.append({
                'type': 'BUY',
                'signal_id': 3,
                'price': doge_price,
                'conditions': signal3_conditions,
                'indicators': {
                    '1h_boll': boll_1h_touch,
                    '15m_boll': boll_15m_touch,
                    '1h_kdj': kdj_1h_val,
                    '15m_kdj': kdj_15m_val,
                    '1m_kdj': kdj_1m_val
                }
            })

        return signals, {
            '1h_boll': boll_1h_touch,
            '15m_boll': boll_15m_touch,
            '1h_kdj': kdj_1h_val,
            '15m_kdj': kdj_15m_val,
            '1m_kdj': kdj_1m_val,
            'price': doge_price
        }

    except Exception as e:
        return [], {}

def main():
    """超详细检查9月17日"""
    print("=" * 80)
    print("超详细检查9月17日 - 5分钟和1分钟间隔")
    print("=" * 80)

    try:
        # 获取更多历史数据
        print("获取历史数据...")
        btc_4h = binance_api.get_klines('BTCUSDT', '4h', 200)
        btc_1h = binance_api.get_klines('BTCUSDT', '1h', 500)
        doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 500)
        doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 1000)
        doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 1000)

        if any(df.empty for df in [btc_4h, btc_1h, doge_1h, doge_15m, doge_1m]):
            print("数据获取失败")
            return

        print(f"数据时间范围:")
        print(f"  BTC 1h: {btc_1h.index[0]} 至 {btc_1h.index[-1]}")
        print(f"  DOGE 1m: {doge_1m.index[0]} 至 {doge_1m.index[-1]}")

        # 初始化技术指标
        boll = BOLL()
        kdj = KDJ()

        # 使用最近一天的数据进行详细分析
        recent_date = doge_1m.index[-1].date()
        target_start = datetime.combine(recent_date, datetime.min.time())
        target_end = datetime.combine(recent_date, datetime.max.time())

        print(f"分析日期: {recent_date}")

        # 两种分析：5分钟间隔 + 1分钟间隔
        for interval_name, interval_minutes in [("5分钟", 5), ("1分钟", 1)]:
            print(f"\n{'-' * 60}")
            print(f"开始{interval_name}间隔分析...")
            print(f"{'-' * 60}")

            # 生成检查点
            current_time = target_start
            check_points = []

            while current_time <= target_end:
                check_points.append(current_time)
                current_time += timedelta(minutes=interval_minutes)

            print(f"检查点数量: {len(check_points)}个 (每{interval_minutes}分钟)")

            signals_found = []
            btc_valid_times = []

            print(f"开始详细分析...")

            for i, check_time in enumerate(check_points):
                # 每1小时显示进度
                if interval_minutes == 5 and i % 12 == 0:  # 5分钟间隔，每小时显示
                    print(f"进度: {i+1}/{len(check_points)} - {check_time.strftime('%H:%M')}")
                elif interval_minutes == 1 and i % 60 == 0:  # 1分钟间隔，每小时显示
                    print(f"进度: {i+1}/{len(check_points)} - {check_time.strftime('%H:%M')}")

                # 检查BTC条件
                btc_result = check_btc_conditions(btc_1h, btc_4h, kdj, check_time)

                if btc_result and btc_result['valid']:
                    btc_valid_times.append(check_time)
                    print(f"\n{check_time.strftime('%H:%M')} BTC条件满足！")
                    print(f"  价格: ${btc_result['price']:,.2f}")
                    print(f"  振幅: {btc_result['volatility']:.2f}% (满足: {btc_result['volatility_ok']})")
                    print(f"  涨跌: {btc_result['change']:.2f}% (满足: {btc_result['growth_ok']})")
                    print(f"  4h KDJ: {btc_result['kdj_4h']:.1f} < 50: {btc_result['kdj_4h'] < 50}")
                    print(f"  1h KDJ: {btc_result['kdj_1h']:.1f} < 50: {btc_result['kdj_1h'] < 50}")

                    # 检查DOGE信号
                    doge_signals, doge_indicators = check_doge_signals(doge_1h, doge_15m, doge_1m, boll, kdj, check_time)

                    print(f"  DOGE指标: 1h布林{doge_indicators.get('1h_boll','无')} KDJ{doge_indicators.get('1h_kdj',0):.1f}, "
                          f"15m布林{doge_indicators.get('15m_boll','无')} KDJ{doge_indicators.get('15m_kdj',0):.1f}, "
                          f"1m KDJ{doge_indicators.get('1m_kdj',0):.1f}")

                    # 详细显示每个信号的条件检查
                    boll_1h_touch = doge_indicators.get('1h_boll', '')
                    boll_15m_touch = doge_indicators.get('15m_boll', '')
                    kdj_1h_val = doge_indicators.get('1h_kdj', 100)
                    kdj_15m_val = doge_indicators.get('15m_kdj', 100)
                    kdj_1m_val = doge_indicators.get('1m_kdj', 100)

                    print(f"  信号1条件: 1h布林DN({boll_1h_touch=='DN'}) + 1hKDJ<10({kdj_1h_val<10}) + 15m布林DN({boll_15m_touch=='DN'}) + 15mKDJ<20({kdj_15m_val<20}) + 1mKDJ<20({kdj_1m_val<20})")
                    print(f"  信号2条件: 1h布林MB({boll_1h_touch=='MB'}) + 1hKDJ<15({kdj_1h_val<15}) + 15m布林DN({boll_15m_touch=='DN'}) + 15mKDJ<20({kdj_15m_val<20}) + 1mKDJ<20({kdj_1m_val<20})")
                    print(f"  信号3条件: 1h布林MB({boll_1h_touch=='MB'}) + 1hKDJ<15({kdj_1h_val<15}) + 15m布林MB({boll_15m_touch=='MB'}) + 15mKDJ<20({kdj_15m_val<20}) + 1mKDJ<20({kdj_1m_val<20})")

                    if doge_signals:
                        for signal in doge_signals:
                            signals_found.append({
                                'time': check_time,
                                'signal': signal
                            })
                            print(f"  *** 发现买入信号{signal['signal_id']}！价格: ${signal['price']:.6f}")

            # 生成当前间隔的报告
            print(f"\n{interval_name}间隔分析结果:")
            print(f"检查点总数: {len(check_points)}个")
            print(f"BTC条件满足: {len(btc_valid_times)}次")
            print(f"发现信号: {len(signals_found)}个")

            if btc_valid_times:
                print(f"BTC条件满足的时段:")
                for time_point in btc_valid_times:
                    print(f"  {time_point.strftime('%H:%M')}")

            if signals_found:
                print(f"发现的买入信号:")
                for item in signals_found:
                    signal = item['signal']
                    time_str = item['time'].strftime('%H:%M')
                    print(f"  {time_str} - 买入信号{signal['signal_id']}: ${signal['price']:.6f}")

        print(f"\n超详细分析完成！")

    except Exception as e:
        print(f"分析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()