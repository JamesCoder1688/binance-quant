#!/usr/bin/env python3
"""
测试技术指标计算
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.indicators.boll import BOLL
from src.indicators.kdj import KDJ
import pandas as pd

def test_doge_indicators():
    """测试DOGE指标计算"""
    print("=== 测试DOGE技术指标 ===")

    try:
        # 获取K线数据
        klines = binance_api.get_klines('DOGEUSDT', '1h', limit=50)
        if klines is None or (hasattr(klines, 'empty') and klines.empty):
            print("❌ 无法获取DOGE K线数据")
            return

        print(f"✅ 获取到 {len(klines)} 条K线数据")

        # 转换数据格式
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]

        print(f"最新价格: ${closes[-1]:.6f}")

        # 测试KDJ计算
        print("\n--- 测试KDJ指标 ---")
        try:
            # 转换为DataFrame
            df = pd.DataFrame({
                'open': [float(k[1]) for k in klines],
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': [float(k[5]) for k in klines]
            })

            kdj = KDJ()
            kdj_df = kdj.calculate(df)
            if not kdj_df.empty:
                latest = kdj_df.iloc[-1]
                print(f"✅ KDJ计算成功")
                print(f"K: {latest['K']:.2f}")
                print(f"D: {latest['D']:.2f}")
                print(f"J: {latest['J']:.2f}")
            else:
                print("❌ KDJ计算失败 - DataFrame为空")
        except Exception as e:
            print(f"❌ KDJ计算失败: {str(e)}")
            import traceback
            traceback.print_exc()

        # 测试BOLL计算
        print("\n--- 测试BOLL指标 ---")
        try:
            # 转换为DataFrame
            df = pd.DataFrame({
                'open': [float(k[1]) for k in klines],
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': [float(k[5]) for k in klines]
            })

            print(f"DataFrame形状: {df.shape}")
            print("DataFrame列:", list(df.columns))

            boll = BOLL()
            boll_df = boll.calculate(df)

            if not boll_df.empty:
                latest = boll_df.iloc[-1]
                print(f"✅ BOLL计算成功")
                print(f"上轨 (UP): ${latest['UP']:.6f}")
                print(f"中轨 (MB): ${latest['MB']:.6f}")
                print(f"下轨 (DN): ${latest['DN']:.6f}")
            else:
                print("❌ BOLL计算失败 - DataFrame为空")

        except Exception as e:
            print(f"❌ BOLL计算失败: {str(e)}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ 整体测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_doge_indicators()