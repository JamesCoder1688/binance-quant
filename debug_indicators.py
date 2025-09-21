#!/usr/bin/env python3
"""
Debug indicator calculations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_doge_indicators():
    """Debug DOGE indicator calculations"""
    print("=== Debug DOGE Indicators ===")

    try:
        from src.data.binance_api import binance_api
        from src.indicators.kdj import KDJ
        from src.indicators.boll import BOLL
        import pandas as pd

        print("✅ All imports successful")

        # Test API connection
        if not binance_api.test_connection():
            print("❌ API connection failed")
            return
        print("✅ API connection successful")

        # Test getting DOGE data
        timeframe = '1h'
        print(f"\n--- Testing {timeframe} data ---")

        df = binance_api.get_klines('DOGEUSDT', timeframe, limit=50)
        print(f"Data type: {type(df)}")

        if df is None:
            print("❌ API returned None")
            return

        if hasattr(df, 'empty') and df.empty:
            print("❌ DataFrame is empty")
            return

        print(f"✅ Data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"Latest close: {df.iloc[-1]['close']:.6f}")

        # Test KDJ calculation
        print("\n--- Testing KDJ ---")
        kdj = KDJ()
        kdj_df = kdj.calculate(df)

        if kdj_df.empty:
            print("❌ KDJ returned empty DataFrame")
        else:
            latest_kdj = kdj_df.iloc[-1]
            print(f"✅ KDJ calculated successfully")
            print(f"K: {latest_kdj['K']:.2f}")
            print(f"D: {latest_kdj['D']:.2f}")
            print(f"J: {latest_kdj['J']:.2f}")

        # Test BOLL calculation
        print("\n--- Testing BOLL ---")
        boll = BOLL()
        boll_df = boll.calculate(df)

        if boll_df.empty:
            print("❌ BOLL returned empty DataFrame")
        else:
            latest_boll = boll_df.iloc[-1]
            print(f"✅ BOLL calculated successfully")
            print(f"Upper: {latest_boll['UP']:.6f}")
            print(f"Middle: {latest_boll['MB']:.6f}")
            print(f"Lower: {latest_boll['DN']:.6f}")

        # Test web monitor function
        print("\n--- Testing WebMonitor.get_doge_detailed_indicators() ---")
        from web_app import web_monitor

        detailed_indicators = web_monitor.get_doge_detailed_indicators()
        print(f"Detailed indicators keys: {list(detailed_indicators.keys())}")

        for key, value in detailed_indicators.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_doge_indicators()