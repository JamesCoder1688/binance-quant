#!/usr/bin/env python3
"""
基础功能测试脚本
测试API连接、技术指标计算和策略逻辑
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.indicators.boll import BOLL
from src.indicators.kdj import KDJ
from src.strategy.btc_monitor import btc_monitor
from src.strategy.doge_signals import doge_signal_generator
from src.utils.logger import logger


def test_api_connection():
    """测试API连接"""
    print("=" * 50)
    print("1. 测试Binance API连接...")

    if binance_api.test_connection():
        print("✅ API连接成功")
        return True
    else:
        print("❌ API连接失败")
        return False


def test_data_fetching():
    """测试数据获取"""
    print("\n2. 测试数据获取...")

    try:
        # 测试获取BTC数据
        btc_data = binance_api.get_klines('BTCUSDT', '1h', 10)
        if not btc_data.empty:
            print(f"✅ BTC 1小时数据获取成功: {len(btc_data)}条记录")
            print(f"   最新价格: {btc_data['close'].iloc[-1]:.2f}")
        else:
            print("❌ BTC数据获取失败")
            return False

        # 测试获取DOGE数据
        doge_data = binance_api.get_klines('DOGEUSDT', '15m', 10)
        if not doge_data.empty:
            print(f"✅ DOGE 15分钟数据获取成功: {len(doge_data)}条记录")
            print(f"   最新价格: {doge_data['close'].iloc[-1]:.6f}")
        else:
            print("❌ DOGE数据获取失败")
            return False

        return True

    except Exception as e:
        print(f"❌ 数据获取测试失败: {str(e)}")
        return False


def test_indicators():
    """测试技术指标计算"""
    print("\n3. 测试技术指标计算...")

    try:
        # 获取测试数据
        data = binance_api.get_klines('BTCUSDT', '1h', 50)
        if data.empty:
            print("❌ 无法获取测试数据")
            return False

        # 测试BOLL指标
        boll = BOLL()
        boll_result = boll.get_latest_values(data)
        if boll_result:
            print(f"✅ BOLL指标计算成功")
            print(f"   UP: {boll_result['UP']:.2f}")
            print(f"   MB: {boll_result['MB']:.2f}")
            print(f"   DN: {boll_result['DN']:.2f}")
            print(f"   触及: {boll_result['touch']}")
        else:
            print("❌ BOLL指标计算失败")
            return False

        # 测试KDJ指标
        kdj = KDJ()
        kdj_result = kdj.get_latest_values(data)
        if kdj_result:
            print(f"✅ KDJ指标计算成功")
            print(f"   K: {kdj_result['K']:.2f}")
            print(f"   D: {kdj_result['D']:.2f}")
            print(f"   J: {kdj_result['J']:.2f}")
            print(f"   MAX: {kdj_result['KDJ_MAX']:.2f}")
        else:
            print("❌ KDJ指标计算失败")
            return False

        return True

    except Exception as e:
        print(f"❌ 技术指标测试失败: {str(e)}")
        return False


def test_btc_monitor():
    """测试BTC监控"""
    print("\n4. 测试BTC监控条件...")

    try:
        # 测试BTC条件检查
        btc_result = btc_monitor.check_all_conditions()

        print(f"✅ BTC监控测试完成")
        print(f"   条件满足: {'是' if btc_result['valid'] else '否'}")

        # 显示详细状态
        status = btc_monitor.get_status_summary()
        print(f"   状态: {status}")

        return True

    except Exception as e:
        print(f"❌ BTC监控测试失败: {str(e)}")
        return False


def test_doge_signals():
    """测试DOGE信号生成"""
    print("\n5. 测试DOGE信号检查...")

    try:
        # 检查买入信号
        buy1 = doge_signal_generator.check_buy_signal_1()
        buy2 = doge_signal_generator.check_buy_signal_2()
        buy3 = doge_signal_generator.check_buy_signal_3()

        print(f"✅ 买入信号检查完成")
        print(f"   买入信号1: {'触发' if buy1.get('signal') else '未触发'}")
        print(f"   买入信号2: {'触发' if buy2.get('signal') else '未触发'}")
        print(f"   买入信号3: {'触发' if buy3.get('signal') else '未触发'}")

        # 检查卖出信号
        sell_signals = doge_signal_generator.check_sell_signals()
        print(f"   卖出信号: {len(sell_signals)}个触发")

        return True

    except Exception as e:
        print(f"❌ DOGE信号测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("🚀 币安量化交易信号生成器 - 基础功能测试")
    print("=" * 50)

    test_results = []

    # 运行所有测试
    test_results.append(test_api_connection())
    test_results.append(test_data_fetching())
    test_results.append(test_indicators())
    test_results.append(test_btc_monitor())
    test_results.append(test_doge_signals())

    # 显示测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"✅ 通过: {sum(test_results)}/5")
    print(f"❌ 失败: {5 - sum(test_results)}/5")

    if all(test_results):
        print("\n🎉 所有基础功能测试通过！系统可以正常运行。")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查网络连接和配置。")
        return False


if __name__ == "__main__":
    main()