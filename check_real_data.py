#!/usr/bin/env python3
"""
检查真实的历史数据，寻找可能的买点
使用真实API数据，按更细的时间间隔检查
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
    """检查真实数据中的买点"""
    print("=" * 80)
    print("检查真实历史数据中的买点")
    print("=" * 80)

    try:
        # 获取更多历史数据
        print("获取完整历史数据...")
        btc_4h = binance_api.get_klines('BTCUSDT', '4h', 1000)
        btc_1h = binance_api.get_klines('BTCUSDT', '1h', 1000)
        doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 1000)
        doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 1000)
        doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 1000)

        if any(df.empty for df in [btc_4h, btc_1h, doge_1h, doge_15m, doge_1m]):
            print("数据获取失败")
            return

        print(f"完整数据时间范围:")
        print(f"  BTC 4h: {btc_4h.index[0]} 至 {btc_4h.index[-1]}")
        print(f"  BTC 1h: {btc_1h.index[0]} 至 {btc_1h.index[-1]}")
        print(f"  DOGE 1h: {doge_1h.index[0]} 至 {doge_1h.index[-1]}")
        print(f"  DOGE 15m: {doge_15m.index[0]} 至 {doge_15m.index[-1]}")
        print(f"  DOGE 1m: {doge_1m.index[0]} 至 {doge_1m.index[-1]}")

        # 初始化技术指标
        boll = BOLL()
        kdj = KDJ()

        signals_found = []
        btc_analysis = []

        print(f"\n开始逐一分析每个1小时数据点...")

        # 从第50个数据点开始分析，确保有足够历史数据
        for i in range(50, len(btc_1h)):
            current_time = btc_1h.index[i]

            if i % 100 == 0:
                print(f"进度: {i}/{len(btc_1h)} - {current_time}")

            # 获取历史数据
            btc_1h_hist = btc_1h.iloc[:i+1].tail(50)
            btc_4h_hist = btc_4h[btc_4h.index <= current_time].tail(20)

            if len(btc_1h_hist) < 25 or len(btc_4h_hist) < 10:
                continue

            # 计算BTC 24小时统计
            recent_24h = btc_1h_hist.tail(24)
            if len(recent_24h) < 20:
                continue

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

            btc_analysis.append({
                'time': current_time,
                'valid': btc_valid,
                'volatility': volatility * 100,
                'change': change_percent * 100,
                'kdj_4h': kdj_4h,
                'kdj_1h': kdj_1h,
                'price': close_price
            })

            if btc_valid:
                print(f"\n{current_time} BTC条件满足！")
                print(f"  价格: ${close_price:,.2f}")
                print(f"  振幅: {volatility*100:.2f}% < 3%: {volatility_ok}")
                print(f"  涨跌: {change_percent*100:.2f}% > 1%: {growth_ok}")
                print(f"  4h KDJ: {kdj_4h:.1f} < 50: {kdj_4h_ok}")
                print(f"  1h KDJ: {kdj_1h:.1f} < 50: {kdj_1h_ok}")

                # 检查DOGE信号
                doge_1h_hist = doge_1h[doge_1h.index <= current_time].tail(50)
                doge_15m_hist = doge_15m[doge_15m.index <= current_time].tail(100)
                doge_1m_hist = doge_1m[doge_1m.index <= current_time].tail(200)

                if len(doge_1h_hist) >= 25 and len(doge_15m_hist) >= 25 and len(doge_1m_hist) >= 25:
                    # 计算DOGE技术指标
                    boll_1h = boll.get_latest_values(doge_1h_hist)
                    boll_15m = boll.get_latest_values(doge_15m_hist)

                    kdj_1h_doge = kdj.get_latest_values(doge_1h_hist)
                    kdj_15m_doge = kdj.get_latest_values(doge_15m_hist)
                    kdj_1m_doge = kdj.get_latest_values(doge_1m_hist)

                    doge_price = doge_1h_hist['close'].iloc[-1]

                    # 显示DOGE技术指标
                    boll_1h_touch = boll_1h.get('touch', '无')
                    boll_15m_touch = boll_15m.get('touch', '无')
                    kdj_1h_val = kdj_1h_doge.get('KDJ_MAX', 100)
                    kdj_15m_val = kdj_15m_doge.get('KDJ_MAX', 100)
                    kdj_1m_val = kdj_1m_doge.get('KDJ_MAX', 100)

                    print(f"  DOGE价格: ${doge_price:.6f}")
                    print(f"  DOGE指标: 1h布林{boll_1h_touch} KDJ{kdj_1h_val:.1f}, "
                          f"15m布林{boll_15m_touch} KDJ{kdj_15m_val:.1f}, 1m KDJ{kdj_1m_val:.1f}")

                    # 检查买入信号1
                    signal1_ok = (boll_1h_touch == 'DN' and kdj_1h_val < 10 and
                                  boll_15m_touch == 'DN' and kdj_15m_val < 20 and kdj_1m_val < 20)

                    # 检查买入信号2
                    signal2_ok = (boll_1h_touch == 'MB' and kdj_1h_val < 15 and
                                  boll_15m_touch == 'DN' and kdj_15m_val < 20 and kdj_1m_val < 20)

                    # 检查买入信号3
                    signal3_ok = (boll_1h_touch == 'MB' and kdj_1h_val < 15 and
                                  boll_15m_touch == 'MB' and kdj_15m_val < 20 and kdj_1m_val < 20)

                    print(f"  信号检查:")
                    print(f"    信号1: 1h布林DN({boll_1h_touch=='DN'}) + 1hKDJ<10({kdj_1h_val<10}) + 15m布林DN({boll_15m_touch=='DN'}) + 15mKDJ<20({kdj_15m_val<20}) + 1mKDJ<20({kdj_1m_val<20}) = {signal1_ok}")
                    print(f"    信号2: 1h布林MB({boll_1h_touch=='MB'}) + 1hKDJ<15({kdj_1h_val<15}) + 15m布林DN({boll_15m_touch=='DN'}) + 15mKDJ<20({kdj_15m_val<20}) + 1mKDJ<20({kdj_1m_val<20}) = {signal2_ok}")
                    print(f"    信号3: 1h布林MB({boll_1h_touch=='MB'}) + 1hKDJ<15({kdj_1h_val<15}) + 15m布林MB({boll_15m_touch=='MB'}) + 15mKDJ<20({kdj_15m_val<20}) + 1mKDJ<20({kdj_1m_val<20}) = {signal3_ok}")

                    if signal1_ok:
                        signals_found.append({
                            'time': current_time,
                            'type': 'BUY',
                            'signal_id': 1,
                            'price': doge_price,
                            'btc_price': close_price
                        })
                        print(f"  *** 发现买入信号1！价格: ${doge_price:.6f}")

                    if signal2_ok:
                        signals_found.append({
                            'time': current_time,
                            'type': 'BUY',
                            'signal_id': 2,
                            'price': doge_price,
                            'btc_price': close_price
                        })
                        print(f"  *** 发现买入信号2！价格: ${doge_price:.6f}")

                    if signal3_ok:
                        signals_found.append({
                            'time': current_time,
                            'type': 'BUY',
                            'signal_id': 3,
                            'price': doge_price,
                            'btc_price': close_price
                        })
                        print(f"  *** 发现买入信号3！价格: ${doge_price:.6f}")

        # 生成最终报告
        print("\n" + "=" * 80)
        print("完整历史数据分析报告")
        print("=" * 80)

        btc_valid_count = sum(1 for item in btc_analysis if item['valid'])

        print(f"总检查数据点: {len(btc_analysis)}个")
        print(f"BTC条件满足: {btc_valid_count}次 ({btc_valid_count/len(btc_analysis)*100:.1f}%)")
        print(f"发现买入信号: {len(signals_found)}个")

        if signals_found:
            print(f"\n发现的所有买入信号:")
            for signal in signals_found:
                time_str = signal['time'].strftime('%Y-%m-%d %H:%M')
                print(f"  {time_str} - 买入信号{signal['signal_id']}: DOGE ${signal['price']:.6f} (BTC ${signal['btc_price']:,.2f})")
        else:
            print(f"\n在整个历史数据中未发现买入信号")
            print(f"这说明您的策略条件确实非常严格，正在等待理想的超卖机会")

        # 统计最有潜力的时段
        if btc_analysis:
            # 找出BTC条件满足但DOGE未触发信号的时段
            btc_valid_times = [item for item in btc_analysis if item['valid']]
            if btc_valid_times:
                print(f"\nBTC条件满足的时段 (最近10次):")
                for item in btc_valid_times[-10:]:
                    time_str = item['time'].strftime('%Y-%m-%d %H:%M')
                    print(f"  {time_str}: BTC ${item['price']:,.2f}, 振幅{item['volatility']:.2f}%, 4hKDJ{item['kdj_4h']:.1f}, 1hKDJ{item['kdj_1h']:.1f}")

        print(f"\n分析完成！")

    except Exception as e:
        print(f"分析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()