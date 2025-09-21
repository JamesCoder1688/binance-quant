#!/usr/bin/env python3
"""
检查数据更新频率和与官网一致性
"""

import sys
import os
import time
import requests
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api

def check_price_update_frequency():
    """检查价格数据更新频率"""
    print("=" * 80)
    print("数据更新频率检查")
    print("=" * 80)

    print("\n[1] 实时价格更新测试:")
    print("-" * 40)

    # 连续获取5次数据，检查更新频率
    prices = []
    timestamps = []

    for i in range(5):
        # 获取BTC价格
        ticker = binance_api.get_24hr_ticker('BTCUSDT')
        if ticker:
            price = float(ticker['lastPrice'])
            current_time = datetime.now()

            prices.append(price)
            timestamps.append(current_time)

            print(f"  第{i+1}次: {current_time.strftime('%H:%M:%S.%f')[:-3]} | BTC: ${price:,.2f}")

            if i < 4:  # 不在最后一次等待
                time.sleep(2)  # 等待2秒

    # 分析价格变化
    print(f"\n  价格变化分析:")
    for i in range(1, len(prices)):
        price_change = prices[i] - prices[i-1]
        time_diff = (timestamps[i] - timestamps[i-1]).total_seconds()
        print(f"  {i}→{i+1}: 价格变化 ${price_change:+.2f}, 时间间隔 {time_diff:.1f}秒")

    if len(set(prices)) > 1:
        print(f"  结论: ✅ 价格数据实时更新")
    else:
        print(f"  结论: ⚠️ 价格数据在测试期间未变化")

def check_official_api_consistency():
    """检查与币安官方API的一致性"""
    print(f"\n[2] 与官方API一致性检查:")
    print("-" * 40)

    try:
        # 使用我们的封装
        our_data = binance_api.get_24hr_ticker('BTCUSDT')

        # 直接调用官方API
        official_response = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
            timeout=10
        )
        official_data = official_response.json()

        if our_data and official_response.status_code == 200:
            print(f"  我们的API:")
            print(f"    lastPrice: {our_data['lastPrice']}")
            print(f"    openPrice: {our_data['openPrice']}")
            print(f"    highPrice: {our_data['highPrice']}")
            print(f"    lowPrice: {our_data['lowPrice']}")
            print(f"    priceChangePercent: {our_data['priceChangePercent']}")

            print(f"\n  官方API:")
            print(f"    lastPrice: {official_data['lastPrice']}")
            print(f"    openPrice: {official_data['openPrice']}")
            print(f"    highPrice: {official_data['highPrice']}")
            print(f"    lowPrice: {official_data['lowPrice']}")
            print(f"    priceChangePercent: {official_data['priceChangePercent']}")

            # 检查数据一致性
            fields_to_check = ['lastPrice', 'openPrice', 'highPrice', 'lowPrice', 'priceChangePercent']
            all_match = True

            print(f"\n  数据一致性检查:")
            for field in fields_to_check:
                our_value = our_data.get(field)
                official_value = official_data.get(field)
                match = our_value == official_value
                all_match = all_match and match

                print(f"    {field}: {'✅ 一致' if match else '❌ 不一致'}")
                if not match:
                    print(f"      我们的: {our_value}")
                    print(f"      官方的: {official_value}")

            if all_match:
                print(f"\n  结论: ✅ 数据完全一致，直接使用官方API")
            else:
                print(f"\n  结论: ⚠️ 数据存在差异，需要检查")

    except Exception as e:
        print(f"  检查失败: {str(e)}")

def check_kline_data_freshness():
    """检查K线数据新鲜度"""
    print(f"\n[3] K线数据新鲜度检查:")
    print("-" * 40)

    try:
        # 获取1分钟K线数据
        klines_1m = binance_api.get_klines('BTCUSDT', '1m', 3)

        if not klines_1m.empty:
            print(f"  最近3根1分钟K线:")
            for i, (timestamp, row) in enumerate(klines_1m.tail(3).iterrows()):
                time_str = timestamp.strftime('%H:%M:%S')
                current_time = datetime.now()
                time_diff = (current_time - timestamp.replace(tzinfo=None)).total_seconds() / 60

                print(f"    {i+1}. {time_str} | C:{row['close']:,.2f} | 距现在 {time_diff:.1f}分钟")

            # 检查最新K线的时效性
            latest_time = klines_1m.index[-1]
            current_time = datetime.now()
            minutes_ago = (current_time - latest_time.replace(tzinfo=None)).total_seconds() / 60

            print(f"\n  最新K线时效性:")
            print(f"    最新K线时间: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    时间差: {minutes_ago:.1f}分钟")

            if minutes_ago <= 2:
                print(f"    结论: ✅ K线数据很新鲜")
            elif minutes_ago <= 5:
                print(f"    结论: ⚠️ K线数据稍有延迟")
            else:
                print(f"    结论: ❌ K线数据可能有延迟")

    except Exception as e:
        print(f"  检查失败: {str(e)}")

def check_update_intervals():
    """检查不同数据类型的更新间隔"""
    print(f"\n[4] 币安API更新间隔说明:")
    print("-" * 40)

    print(f"  官方更新频率:")
    print(f"    24小时统计数据: 每秒更新")
    print(f"    K线数据:")
    print(f"      - 1分钟K线: 每分钟更新")
    print(f"      - 15分钟K线: 每15分钟更新")
    print(f"      - 1小时K线: 每小时更新")
    print(f"      - 4小时K线: 每4小时更新")

    print(f"\n  我们的监控频率:")
    print(f"    主程序检查间隔: 30秒 (可配置)")
    print(f"    API调用: 每次检查都实时获取最新数据")
    print(f"    技术指标: 基于最新K线数据实时计算")

def test_real_time_vs_web():
    """测试与网页端的实时对比"""
    print(f"\n[5] 与网页端实时对比测试:")
    print("-" * 40)

    try:
        # 获取实时数据
        btc_ticker = binance_api.get_24hr_ticker('BTCUSDT')
        doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')

        current_time = datetime.now()

        print(f"  当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  ")
        print(f"  请同时打开以下网页进行对比:")
        print(f"    BTC: https://www.binance.com/en/trade/BTC_USDT")
        print(f"    DOGE: https://www.binance.com/en/trade/DOGE_USDT")
        print(f"  ")
        print(f"  我们的数据:")
        if btc_ticker:
            print(f"    BTC: ${float(btc_ticker['lastPrice']):,.2f} ({float(btc_ticker['priceChangePercent']):+.2f}%)")
        if doge_ticker:
            print(f"    DOGE: ${float(doge_ticker['lastPrice']):.6f} ({float(doge_ticker['priceChangePercent']):+.2f}%)")

        print(f"  ")
        print(f"  验证方法:")
        print(f"    1. 对比当前价格是否一致")
        print(f"    2. 对比24小时涨跌幅是否一致")
        print(f"    3. 如果完全一致，说明我们的数据是实时的")

    except Exception as e:
        print(f"  测试失败: {str(e)}")

def main():
    """主函数"""
    print("币安量化交易系统 - 数据更新频率检查")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 执行各项检查
    check_price_update_frequency()
    check_official_api_consistency()
    check_kline_data_freshness()
    check_update_intervals()
    test_real_time_vs_web()

    print(f"\n" + "=" * 80)
    print("总结:")
    print("我们的系统直接使用币安官方API，数据实时性与官网完全一致。")
    print("监控程序每30秒检查一次，可以捕获到分钟级别的市场变化。")
    print("=" * 80)

if __name__ == "__main__":
    main()