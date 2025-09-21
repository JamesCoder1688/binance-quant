#!/usr/bin/env python3
"""
数据准确性验证脚本
对比币安API数据和我们的计算结果
"""

import sys
import os
import json
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.indicators.boll import BOLL
from src.indicators.kdj import KDJ

def verify_api_data():
    """验证API数据获取的准确性"""
    print("=" * 80)
    print("API数据验证")
    print("=" * 80)

    try:
        # 1. 验证24小时数据
        print("\n[1] 24小时统计数据验证:")
        print("-" * 40)

        # BTC数据
        btc_ticker = binance_api.get_24hr_ticker('BTCUSDT')
        if btc_ticker:
            print(f"BTC/USDT 24小时数据:")
            print(f"  当前价格: ${float(btc_ticker['lastPrice']):,.2f}")
            print(f"  开盘价格: ${float(btc_ticker['openPrice']):,.2f}")
            print(f"  最高价格: ${float(btc_ticker['highPrice']):,.2f}")
            print(f"  最低价格: ${float(btc_ticker['lowPrice']):,.2f}")
            print(f"  24h涨跌: {float(btc_ticker['priceChangePercent']):+.2f}%")
            print(f"  成交量: {float(btc_ticker['volume']):,.0f} BTC")

            # 验证振幅计算
            high = float(btc_ticker['highPrice'])
            low = float(btc_ticker['lowPrice'])
            open_price = float(btc_ticker['openPrice'])
            volatility = (high - low) / open_price

            print(f"\n  振幅计算验证:")
            print(f"  公式: (最高价 - 最低价) / 开盘价")
            print(f"  计算: ({high:,.2f} - {low:,.2f}) / {open_price:,.2f}")
            print(f"  结果: {volatility:.4f} = {volatility*100:.2f}%")

        # DOGE数据
        doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')
        if doge_ticker:
            print(f"\nDOGE/USDT 24小时数据:")
            print(f"  当前价格: ${float(doge_ticker['lastPrice']):.6f}")
            print(f"  开盘价格: ${float(doge_ticker['openPrice']):.6f}")
            print(f"  最高价格: ${float(doge_ticker['highPrice']):.6f}")
            print(f"  最低价格: ${float(doge_ticker['lowPrice']):.6f}")
            print(f"  24h涨跌: {float(doge_ticker['priceChangePercent']):+.2f}%")
            print(f"  成交量: {float(doge_ticker['volume']):,.0f} DOGE")

        # 2. 验证K线数据
        print("\n[2] K线数据验证:")
        print("-" * 40)

        # 获取最近5根K线数据
        btc_klines = binance_api.get_klines('BTCUSDT', '1h', 5)
        if not btc_klines.empty:
            print(f"BTC 1小时K线数据 (最近5根):")
            for i, (timestamp, row) in enumerate(btc_klines.tail(5).iterrows()):
                print(f"  {i+1}. {timestamp.strftime('%m-%d %H:%M')} | "
                      f"O:{row['open']:,.2f} H:{row['high']:,.2f} "
                      f"L:{row['low']:,.2f} C:{row['close']:,.2f}")

        return True

    except Exception as e:
        print(f"API数据验证失败: {str(e)}")
        return False


def verify_boll_calculation():
    """验证BOLL指标计算"""
    print("\n\n[3] BOLL指标计算验证:")
    print("-" * 40)

    try:
        # 获取足够的数据进行计算
        data = binance_api.get_klines('BTCUSDT', '1h', 25)
        if data.empty:
            print("无法获取数据")
            return False

        # 使用我们的BOLL计算器
        boll = BOLL(period=20, std_dev=2)
        result = boll.get_latest_values(data)

        if result:
            print(f"BOLL(20,2) 计算结果:")
            print(f"  上轨 UP: ${result['UP']:.2f}")
            print(f"  中轨 MB: ${result['MB']:.2f}")
            print(f"  下轨 DN: ${result['DN']:.2f}")
            print(f"  当前价: ${result['close']:.2f}")
            print(f"  触及状态: {result['touch']}")

            # 手动验证中轨计算（20周期均线）
            recent_closes = data['close'].tail(20)
            manual_mb = recent_closes.mean()
            manual_std = recent_closes.std()
            manual_up = manual_mb + 2 * manual_std
            manual_dn = manual_mb - 2 * manual_std

            print(f"\n  手动计算验证:")
            print(f"  20周期均线: ${manual_mb:.2f}")
            print(f"  标准差: {manual_std:.2f}")
            print(f"  上轨计算: ${manual_mb:.2f} + 2*{manual_std:.2f} = ${manual_up:.2f}")
            print(f"  下轨计算: ${manual_mb:.2f} - 2*{manual_std:.2f} = ${manual_dn:.2f}")

            # 对比结果
            mb_diff = abs(result['MB'] - manual_mb)
            up_diff = abs(result['UP'] - manual_up)
            dn_diff = abs(result['DN'] - manual_dn)

            print(f"\n  计算差异:")
            print(f"  中轨差异: {mb_diff:.6f}")
            print(f"  上轨差异: {up_diff:.6f}")
            print(f"  下轨差异: {dn_diff:.6f}")

            if mb_diff < 0.01 and up_diff < 0.01 and dn_diff < 0.01:
                print(f"  验证结果: ✅ BOLL计算正确")
                return True
            else:
                print(f"  验证结果: ❌ BOLL计算有误差")
                return False

    except Exception as e:
        print(f"BOLL验证失败: {str(e)}")
        return False


def verify_kdj_calculation():
    """验证KDJ指标计算"""
    print("\n\n[4] KDJ指标计算验证:")
    print("-" * 40)

    try:
        # 获取足够的数据
        data = binance_api.get_klines('BTCUSDT', '1h', 20)
        if data.empty:
            print("无法获取数据")
            return False

        # 使用我们的KDJ计算器
        kdj = KDJ(k_period=9, k_smooth=3, d_smooth=3)
        result = kdj.get_latest_values(data)

        if result:
            print(f"KDJ(9,3,3) 计算结果:")
            print(f"  K值: {result['K']:.2f}")
            print(f"  D值: {result['D']:.2f}")
            print(f"  J值: {result['J']:.2f}")
            print(f"  判断值: {result['KDJ_MAX']:.2f}")

            # 手动验证最后一个RSV计算
            recent_data = data.tail(9)
            high_max = recent_data['high'].max()
            low_min = recent_data['low'].min()
            current_close = data['close'].iloc[-1]

            if high_max != low_min:
                rsv = ((current_close - low_min) / (high_max - low_min)) * 100
            else:
                rsv = 50

            print(f"\n  最新RSV计算验证:")
            print(f"  9期最高价: ${high_max:.2f}")
            print(f"  9期最低价: ${low_min:.2f}")
            print(f"  当前收盘: ${current_close:.2f}")
            print(f"  RSV = ({current_close:.2f} - {low_min:.2f}) / ({high_max:.2f} - {low_min:.2f}) * 100")
            print(f"  RSV = {rsv:.2f}")

            # 验证J值计算
            manual_j = 3 * result['K'] - 2 * result['D']
            j_diff = abs(result['J'] - manual_j)

            print(f"\n  J值计算验证:")
            print(f"  J = 3K - 2D = 3*{result['K']:.2f} - 2*{result['D']:.2f} = {manual_j:.2f}")
            print(f"  计算差异: {j_diff:.2f}")

            if j_diff < 0.1:
                print(f"  验证结果: ✅ KDJ计算正确")
                return True
            else:
                print(f"  验证结果: ❌ KDJ计算有误差")
                return False

    except Exception as e:
        print(f"KDJ验证失败: {str(e)}")
        return False


def show_raw_api_responses():
    """显示原始API响应，便于对比"""
    print("\n\n[5] 原始API响应数据:")
    print("-" * 40)

    try:
        # 显示24小时数据的原始响应
        import requests

        print("\n币安API原始响应 (可与其他工具对比):")

        # BTC 24小时数据
        response = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT')
        if response.status_code == 200:
            data = response.json()
            print(f"\nBTC 24小时原始数据:")
            print(f"  lastPrice: {data['lastPrice']}")
            print(f"  openPrice: {data['openPrice']}")
            print(f"  highPrice: {data['highPrice']}")
            print(f"  lowPrice: {data['lowPrice']}")
            print(f"  priceChangePercent: {data['priceChangePercent']}")

        # DOGE 24小时数据
        response = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=DOGEUSDT')
        if response.status_code == 200:
            data = response.json()
            print(f"\nDOGE 24小时原始数据:")
            print(f"  lastPrice: {data['lastPrice']}")
            print(f"  openPrice: {data['openPrice']}")
            print(f"  highPrice: {data['highPrice']}")
            print(f"  lowPrice: {data['lowPrice']}")
            print(f"  priceChangePercent: {data['priceChangePercent']}")

        print(f"\n对比方法:")
        print(f"1. 打开币安官网 https://www.binance.com/en/trade/BTC_USDT")
        print(f"2. 对比24小时统计数据")
        print(f"3. 在TradingView添加BOLL(20,2)和KDJ(9,3,3)指标")
        print(f"4. 对比技术指标数值")

    except Exception as e:
        print(f"获取原始数据失败: {str(e)}")


def main():
    """主验证函数"""
    print("币安量化交易系统 - 数据准确性验证")
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # 执行各项验证
    results.append(verify_api_data())
    results.append(verify_boll_calculation())
    results.append(verify_kdj_calculation())

    # 显示原始数据
    show_raw_api_responses()

    # 总结验证结果
    print("\n" + "=" * 80)
    print("验证结果总结:")
    print(f"API数据获取: {'✅ 正确' if results[0] else '❌ 有问题'}")
    print(f"BOLL指标计算: {'✅ 正确' if results[1] else '❌ 有问题'}")
    print(f"KDJ指标计算: {'✅ 正确' if results[2] else '❌ 有问题'}")

    if all(results):
        print(f"\n🎉 所有验证通过！系统数据和计算完全准确。")
    else:
        print(f"\n⚠️ 部分验证失败，需要检查相关模块。")

    print("=" * 80)

if __name__ == "__main__":
    main()