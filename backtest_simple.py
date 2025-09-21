#!/usr/bin/env python3
"""
简化历史数据回测 - 测试交易策略
从9月12日以来的历史数据测试买卖点
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
    """简化回测主函数"""
    print("=" * 60)
    print("策略回测 - 9月12日以来历史数据")
    print("=" * 60)

    # 计算从9月12日到现在的天数
    start_date = datetime(2024, 9, 12)
    current_date = datetime.now()
    days_since = (current_date - start_date).days

    print(f"回测期间: 9月12日至今 ({days_since}天)")
    print(f"数据获取策略: 获取最大可用历史数据")

    try:
        # 获取最大历史数据（1000条限制）
        print("\n获取历史数据...")

        print("获取BTC数据...")
        btc_4h = binance_api.get_klines('BTCUSDT', '4h', 1000)
        btc_1h = binance_api.get_klines('BTCUSDT', '1h', 1000)

        print("获取DOGE数据...")
        doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 1000)
        doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 1000)
        doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 1000)

        if any(df.empty for df in [btc_4h, btc_1h, doge_1h, doge_15m, doge_1m]):
            print("数据获取失败")
            return

        print(f"BTC 4h: {len(btc_4h)}条, BTC 1h: {len(btc_1h)}条")
        print(f"DOGE 1h: {len(doge_1h)}条, DOGE 15m: {len(doge_15m)}条, DOGE 1m: {len(doge_1m)}条")

        # 初始化技术指标
        boll = BOLL()
        kdj = KDJ()

        signals = []
        btc_conditions = []

        # 显示数据时间范围
        print(f"BTC 4h数据: {len(btc_4h)}条，时间范围: {btc_4h.index[0]} 至 {btc_4h.index[-1]}")
        print(f"BTC 1h数据: {len(btc_1h)}条，时间范围: {btc_1h.index[0]} 至 {btc_1h.index[-1]}")
        print(f"DOGE数据: 1h({len(doge_1h)}条), 15m({len(doge_15m)}条), 1m({len(doge_1m)}条)")

        # 确定回测范围：严格从9月12日开始
        target_start = datetime(2024, 9, 12)
        end_time = datetime.now() - timedelta(hours=1)

        # 过滤数据，只保留9月12日之后的
        btc_4h_filtered = btc_4h[btc_4h.index >= target_start]
        btc_1h_filtered = btc_1h[btc_1h.index >= target_start]
        doge_1h_filtered = doge_1h[doge_1h.index >= target_start]
        doge_15m_filtered = doge_15m[doge_15m.index >= target_start]
        doge_1m_filtered = doge_1m[doge_1m.index >= target_start]

        print(f"9月12日后可用数据:")
        print(f"  BTC 4h: {len(btc_4h_filtered)}条")
        print(f"  BTC 1h: {len(btc_1h_filtered)}条")
        print(f"  DOGE: 1h({len(doge_1h_filtered)}条), 15m({len(doge_15m_filtered)}条), 1m({len(doge_1m_filtered)}条)")

        if any(df.empty for df in [btc_4h_filtered, btc_1h_filtered, doge_1h_filtered]):
            print("9月12日后没有足够数据")
            return

        print(f"回测时间范围: {target_start} 至 {end_time}")

        # 回测从9月12日到1小时前（每小时检查一次）
        print("\n开始回测分析...")

        start_time = target_start

        current_time = start_time
        check_count = 0
        btc_valid_count = 0

        # 计算总检查次数
        total_hours = int((end_time - start_time).total_seconds() / 3600)
        print(f"计划检查 {total_hours} 个时间点...")

        while current_time <= end_time:
            check_count += 1

            # 每检查100次显示进度
            if check_count % 100 == 0 or check_count == 1:
                progress = (check_count / total_hours) * 100 if total_hours > 0 else 0
                print(f"进度: {check_count}/{total_hours} ({progress:.1f}%) - {current_time.strftime('%m-%d %H:%M')}")

            # 获取当前时间点的数据（使用过滤后的数据）
            btc_1h_recent = btc_1h_filtered[btc_1h_filtered.index <= current_time].tail(50)
            btc_4h_recent = btc_4h_filtered[btc_4h_filtered.index <= current_time].tail(50)

            if len(btc_1h_recent) < 25 or len(btc_4h_recent) < 10:
                current_time += timedelta(hours=1)
                continue

            # 计算BTC 24小时统计
            recent_24h = btc_1h_recent.tail(24)
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
                kdj_4h_values = kdj.get_latest_values(btc_4h_recent)
                kdj_1h_values = kdj.get_latest_values(btc_1h_recent)

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
                    print(f"{current_time.strftime('%m-%d %H:%M')} BTC条件满足，检查DOGE信号...")

                    # 检查DOGE信号（使用过滤后的数据）
                    doge_1h_recent = doge_1h_filtered[doge_1h_filtered.index <= current_time].tail(50)
                    doge_15m_recent = doge_15m_filtered[doge_15m_filtered.index <= current_time].tail(50)
                    doge_1m_recent = doge_1m_filtered[doge_1m_filtered.index <= current_time].tail(50)

                    if len(doge_1h_recent) >= 25 and len(doge_15m_recent) >= 25 and len(doge_1m_recent) >= 25:
                        # 计算DOGE技术指标
                        boll_1h = boll.get_latest_values(doge_1h_recent)
                        boll_15m = boll.get_latest_values(doge_15m_recent)

                        kdj_1h_doge = kdj.get_latest_values(doge_1h_recent)
                        kdj_15m_doge = kdj.get_latest_values(doge_15m_recent)
                        kdj_1m_doge = kdj.get_latest_values(doge_1m_recent)

                        doge_price = doge_1h_recent['close'].iloc[-1]

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
                                'price': doge_price,
                                'conditions': f"1h布林DN KDJ{kdj_1h_doge.get('KDJ_MAX',0):.1f}, 15m布林DN KDJ{kdj_15m_doge.get('KDJ_MAX',0):.1f}, 1m KDJ{kdj_1m_doge.get('KDJ_MAX',0):.1f}"
                            }
                            signals.append(signal)
                            print(f"  *** BUY Signal 1: ${doge_price:.6f}")

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
                                'price': doge_price,
                                'conditions': f"1h布林MB KDJ{kdj_1h_doge.get('KDJ_MAX',0):.1f}, 15m布林DN KDJ{kdj_15m_doge.get('KDJ_MAX',0):.1f}, 1m KDJ{kdj_1m_doge.get('KDJ_MAX',0):.1f}"
                            }
                            signals.append(signal)
                            print(f"  *** BUY Signal 2: ${doge_price:.6f}")

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
                                'price': doge_price,
                                'conditions': f"1h布林MB KDJ{kdj_1h_doge.get('KDJ_MAX',0):.1f}, 15m布林MB KDJ{kdj_15m_doge.get('KDJ_MAX',0):.1f}, 1m KDJ{kdj_1m_doge.get('KDJ_MAX',0):.1f}"
                            }
                            signals.append(signal)
                            print(f"  *** BUY Signal 3: ${doge_price:.6f}")

            # 下一个小时
            current_time += timedelta(hours=1)

        # 生成报告
        print("\n" + "=" * 60)
        print("回测报告")
        print("=" * 60)

        buy_signals = [s for s in signals if s['type'] == 'BUY']
        sell_signals = [s for s in signals if s['type'] == 'SELL']

        print(f"总检查次数: {check_count}")
        print(f"BTC条件满足次数: {btc_valid_count} ({btc_valid_count/check_count*100:.1f}%)")
        print(f"买入信号总数: {len(buy_signals)}")
        print(f"卖出信号总数: {len(sell_signals)}")

        if buy_signals:
            print(f"\n买入信号详情:")
            for signal in buy_signals:
                print(f"  {signal['time']} - 买入信号{signal['signal_id']}: ${signal['price']:.6f}")
                print(f"    {signal['conditions']}")

        # BTC条件统计
        if btc_conditions:
            avg_volatility = sum(c['volatility'] for c in btc_conditions) / len(btc_conditions)
            avg_change = sum(c['change'] for c in btc_conditions) / len(btc_conditions)
            avg_kdj_4h = sum(c['kdj_4h'] for c in btc_conditions) / len(btc_conditions)
            avg_kdj_1h = sum(c['kdj_1h'] for c in btc_conditions) / len(btc_conditions)

            print(f"\nBTC条件统计 (24小时平均):")
            print(f"  平均振幅: {avg_volatility:.2f}%")
            print(f"  平均涨跌: {avg_change:.2f}%")
            print(f"  平均4h KDJ: {avg_kdj_4h:.1f}")
            print(f"  平均1h KDJ: {avg_kdj_1h:.1f}")

        print(f"\n回测完成！发现 {len(signals)} 个交易信号")

    except Exception as e:
        print(f"回测失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()