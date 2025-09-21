#!/usr/bin/env python3
"""
直接测试web应用中的指标计算函数
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.indicators.boll import BOLL
from src.indicators.kdj import KDJ
import pandas as pd

def test_web_app_doge_function():
    """测试web应用中的DOGE指标函数"""
    print("=== 测试Web应用DOGE指标函数 ===")

    try:
        from src.indicators.kdj import KDJ
        from src.indicators.boll import BOLL
        import pandas as pd

        indicators = {}

        # 获取多时间框架的BOLL和KDJ数据
        for timeframe in ['1h']:  # 只测试1小时
            print(f"\n--- 测试 {timeframe} 时间框架 ---")
            try:
                # 获取K线数据 (已经是DataFrame格式)
                df = binance_api.get_klines('DOGEUSDT', timeframe, limit=50)
                print(f"API返回数据类型: {type(df)}")

                if df is None:
                    print("❌ API返回None")
                    continue
                elif hasattr(df, 'empty') and df.empty:
                    print("❌ DataFrame为空")
                    continue

                print(f"✅ 获取数据成功，形状: {df.shape}")
                print(f"列名: {list(df.columns)}")
                print(f"最新收盘价: {df.iloc[-1]['close']:.6f}")

                # 计算KDJ指标
                try:
                    print("\n测试KDJ计算...")
                    kdj = KDJ()
                    kdj_df = kdj.calculate(df)
                    if not kdj_df.empty:
                        latest_kdj = kdj_df.iloc[-1]
                        indicators[f'kdj_{timeframe}'] = {
                            'k': float(round(latest_kdj['K'], 2)),
                            'd': float(round(latest_kdj['D'], 2)),
                            'j': float(round(latest_kdj['J'], 2))
                        }
                        print(f"✅ KDJ计算成功: {indicators[f'kdj_{timeframe}']}")
                    else:
                        print("❌ KDJ返回空DataFrame")
                except Exception as e:
                    print(f"❌ KDJ计算失败: {str(e)}")
                    import traceback
                    traceback.print_exc()

                # 计算BOLL指标
                try:
                    print("\n测试BOLL计算...")
                    boll = BOLL()
                    boll_df = boll.calculate(df)
                    if not boll_df.empty:
                        latest_boll = boll_df.iloc[-1]
                        indicators[f'boll_{timeframe}'] = {
                            'upper': float(round(latest_boll['UP'], 6)),
                            'middle': float(round(latest_boll['MB'], 6)),
                            'lower': float(round(latest_boll['DN'], 6)),
                            'current_price': float(round(df.iloc[-1]['close'], 6)),
                            'position': str('above' if df.iloc[-1]['close'] > latest_boll['UP'] else 'below' if df.iloc[-1]['close'] < latest_boll['DN'] else 'inside')
                        }
                        print(f"✅ BOLL计算成功: {indicators[f'boll_{timeframe}']}")
                    else:
                        print("❌ BOLL返回空DataFrame")
                except Exception as e:
                    print(f"❌ BOLL计算失败: {str(e)}")
                    import traceback
                    traceback.print_exc()

            except Exception as e:
                print(f"❌ {timeframe} 指标计算失败: {str(e)}")
                import traceback
                traceback.print_exc()

        print(f"\n=== 最终结果 ===")
        print(f"计算出的指标: {list(indicators.keys())}")
        for key, value in indicators.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"❌ 整体测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_app_doge_function()