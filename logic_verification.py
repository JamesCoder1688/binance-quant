#!/usr/bin/env python3
"""
逻辑验证监控 - 显示详细计算过程
用于验证监控程序的计算逻辑是否正确
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

def show_calculation_details():
    """显示详细计算过程"""
    current_time = datetime.now().strftime('%H:%M:%S')
    print("=" * 100)
    print(f"计算逻辑验证 - {current_time}")
    print("=" * 100)

    try:
        # 1. 获取基础价格数据
        print("\n[1] 基础价格数据:")
        print("-" * 50)

        btc_ticker = binance_api.get_24hr_ticker('BTCUSDT')
        doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')

        if btc_ticker and doge_ticker:
            btc_price = float(btc_ticker['lastPrice'])
            btc_open = float(btc_ticker['openPrice'])
            btc_high = float(btc_ticker['highPrice'])
            btc_low = float(btc_ticker['lowPrice'])
            btc_change = float(btc_ticker['priceChangePercent'])

            doge_price = float(doge_ticker['lastPrice'])
            doge_change = float(doge_ticker['priceChangePercent'])

            print(f"BTC当前价格: ${btc_price:,.2f}")
            print(f"BTC 24h数据: 开盘${btc_open:,.2f}, 最高${btc_high:,.2f}, 最低${btc_low:,.2f}")
            print(f"BTC 24h涨跌: {btc_change:+.2f}%")
            print(f"DOGE当前价格: ${doge_price:.6f} ({doge_change:+.2f}%)")

        # 2. BTC振幅计算验证
        print(f"\n[2] BTC振幅计算验证:")
        print("-" * 50)

        volatility = (btc_high - btc_low) / btc_open
        volatility_percent = volatility * 100
        growth_percent = btc_change

        print(f"振幅公式: (最高价 - 最低价) / 开盘价")
        print(f"振幅计算: ({btc_high:,.2f} - {btc_low:,.2f}) / {btc_open:,.2f}")
        print(f"振幅结果: {volatility:.4f} = {volatility_percent:.2f}%")
        print(f"涨幅数据: {growth_percent:+.2f}%")

        # 振幅和涨幅条件检查
        volatility_ok = volatility_percent < 3.0
        growth_ok = growth_percent > 1.0
        condition_24h = volatility_ok or growth_ok

        print(f"振幅条件: {volatility_percent:.2f}% < 3.0% = {volatility_ok}")
        print(f"涨幅条件: {growth_percent:.2f}% > 1.0% = {growth_ok}")
        print(f"24h条件: {volatility_ok} OR {growth_ok} = {condition_24h}")

        # 3. BTC KDJ计算验证
        print(f"\n[3] BTC KDJ计算验证:")
        print("-" * 50)

        # 获取4小时和1小时数据
        btc_4h = binance_api.get_klines('BTCUSDT', '4h', 50)
        btc_1h = binance_api.get_klines('BTCUSDT', '1h', 50)

        kdj = KDJ()

        if not btc_4h.empty:
            kdj_4h_values = kdj.get_latest_values(btc_4h)
            k_4h = kdj_4h_values.get('K', 0)
            d_4h = kdj_4h_values.get('D', 0)
            j_4h = kdj_4h_values.get('J', 0)
            max_4h = kdj_4h_values.get('KDJ_MAX', 0)

            print(f"4小时KDJ: K={k_4h:.2f}, D={d_4h:.2f}, J={j_4h:.2f}")
            print(f"4小时判断值: max({k_4h:.2f}, {d_4h:.2f}, {j_4h:.2f}) = {max_4h:.2f}")

            # 验证J值计算
            manual_j_4h = 3 * k_4h - 2 * d_4h
            print(f"J值验证: 3×{k_4h:.2f} - 2×{d_4h:.2f} = {manual_j_4h:.2f} {'✓' if abs(manual_j_4h - j_4h) < 0.1 else '✗'}")

        if not btc_1h.empty:
            kdj_1h_values = kdj.get_latest_values(btc_1h)
            k_1h = kdj_1h_values.get('K', 0)
            d_1h = kdj_1h_values.get('D', 0)
            j_1h = kdj_1h_values.get('J', 0)
            max_1h = kdj_1h_values.get('KDJ_MAX', 0)

            print(f"1小时KDJ: K={k_1h:.2f}, D={d_1h:.2f}, J={j_1h:.2f}")
            print(f"1小时判断值: max({k_1h:.2f}, {d_1h:.2f}, {j_1h:.2f}) = {max_1h:.2f}")

            # 验证J值计算
            manual_j_1h = 3 * k_1h - 2 * d_1h
            print(f"J值验证: 3×{k_1h:.2f} - 2×{d_1h:.2f} = {manual_j_1h:.2f} {'✓' if abs(manual_j_1h - j_1h) < 0.1 else '✗'}")

        # 4. BTC策略条件综合判断
        print(f"\n[4] BTC策略条件综合判断:")
        print("-" * 50)

        kdj_4h_ok = max_4h < 20
        kdj_1h_ok = max_1h < 20
        kdj_condition = kdj_4h_ok and kdj_1h_ok

        print(f"新策略KDJ条件:")
        print(f"4小时KDJ<20: {max_4h:.2f} < 20 = {kdj_4h_ok}")
        print(f"1小时KDJ<20: {max_1h:.2f} < 20 = {kdj_1h_ok}")
        print(f"KDJ条件: {kdj_4h_ok} AND {kdj_1h_ok} = {kdj_condition}")

        # 最终BTC条件
        btc_final = condition_24h and kdj_condition
        print(f"BTC最终条件: {condition_24h} AND {kdj_condition} = {btc_final}")
        print(f"BTC策略状态: {'✓ 满足' if btc_final else '✗ 不满足'}")

        # 5. DOGE技术指标计算
        print(f"\n[5] DOGE技术指标计算:")
        print("-" * 50)

        # 获取DOGE数据
        doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 50)
        doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 50)
        doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 50)

        boll = BOLL()

        # DOGE 1小时指标
        if not doge_1h.empty:
            boll_1h = boll.get_latest_values(doge_1h)
            kdj_1h_doge = kdj.get_latest_values(doge_1h)

            print(f"DOGE 1小时BOLL:")
            print(f"  UP=${boll_1h.get('UP', 0):.6f}, MB=${boll_1h.get('MB', 0):.6f}, DN=${boll_1h.get('DN', 0):.6f}")
            print(f"  当前价格=${boll_1h.get('close', 0):.6f}")
            print(f"  触及状态: {boll_1h.get('touch', '无')}")
            print(f"DOGE 1小时KDJ: {kdj_1h_doge.get('KDJ_MAX', 0):.2f}")

        # DOGE 15分钟指标
        if not doge_15m.empty:
            boll_15m = boll.get_latest_values(doge_15m)
            kdj_15m_doge = kdj.get_latest_values(doge_15m)

            print(f"DOGE 15分钟BOLL: 触及{boll_15m.get('touch', '无')}")
            print(f"DOGE 15分钟KDJ: {kdj_15m_doge.get('KDJ_MAX', 0):.2f}")

        # DOGE 1分钟指标
        if not doge_1m.empty:
            kdj_1m_doge = kdj.get_latest_values(doge_1m)
            print(f"DOGE 1分钟KDJ: {kdj_1m_doge.get('KDJ_MAX', 0):.2f}")

        # 6. 买卖信号逻辑验证
        print(f"\n[6] 买卖信号逻辑验证:")
        print("-" * 50)

        if btc_final:
            print("BTC条件满足，检查DOGE买入信号...")

            # 买入信号1检查
            if 'boll_1h' in locals() and 'kdj_1h_doge' in locals():
                signal1_conditions = {
                    '1h_dn': boll_1h.get('touch') == 'DN',
                    '1h_kdj10': kdj_1h_doge.get('KDJ_MAX', 100) < 10,
                    '15m_dn': boll_15m.get('touch') == 'DN' if 'boll_15m' in locals() else False,
                    '15m_kdj10': kdj_15m_doge.get('KDJ_MAX', 100) < 10 if 'kdj_15m_doge' in locals() else False,
                    '1m_kdj20': kdj_1m_doge.get('KDJ_MAX', 100) < 20 if 'kdj_1m_doge' in locals() else False
                }

                print("买入信号1条件:")
                for condition, result in signal1_conditions.items():
                    print(f"  {condition}: {result}")

                signal1_trigger = all(signal1_conditions.values())
                print(f"买入信号1: {'触发' if signal1_trigger else '未触发'}")
        else:
            print("BTC条件不满足，无需检查DOGE信号")

        # 7. 系统实际结果对比
        print(f"\n[7] 系统实际结果对比:")
        print("-" * 50)

        # 获取系统实际计算结果
        btc_system = btc_monitor.check_all_conditions()
        signals_system = doge_signal_generator.check_all_signals()

        print(f"系统BTC条件: {btc_system['valid']}")
        print(f"手动BTC条件: {btc_final}")
        print(f"BTC条件一致性: {'✓' if btc_system['valid'] == btc_final else '✗'}")

        if signals_system:
            print(f"系统检测信号: {len(signals_system)}个")
            for signal in signals_system:
                signal_type = signal.get('type', 'unknown').upper()
                signal_id = signal.get('signal_id', 0)
                print(f"  {signal_type} Signal {signal_id}")
        else:
            print(f"系统检测信号: 无")

        print("\n" + "=" * 100)
        print("逻辑验证完成! 您可以对比手动计算和系统计算的结果是否一致。")

    except Exception as e:
        print(f"验证过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("计算逻辑验证监控")
    print("将显示详细的计算过程，用于验证监控程序逻辑")
    print("按 Ctrl+C 停止监控")

    try:
        cycle = 0
        while cycle < 3:  # 运行3次验证
            show_calculation_details()
            cycle += 1

            if cycle < 3:
                print(f"\n等待10秒后进行下一次验证... ({cycle}/3)")
                time.sleep(10)

        print("\n验证完成!")

    except KeyboardInterrupt:
        print("\n验证已停止")

if __name__ == "__main__":
    main()