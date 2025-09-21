#!/usr/bin/env python3
"""
Test web monitor function directly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_web_monitor():
    """Test web monitor DOGE indicators function"""
    print("=== Testing WebMonitor DOGE indicators ===")

    try:
        # Import the web monitor class directly
        sys.path.append('.')
        from web_app import WebMonitor

        # Create instance
        monitor = WebMonitor()
        print("✅ WebMonitor created successfully")

        # Test DOGE data
        print("\n--- Testing get_doge_data() ---")
        doge_data = monitor.get_doge_data()
        print(f"DOGE data type: {type(doge_data)}")
        print(f"DOGE data keys: {list(doge_data.keys())}")

        if 'error' in doge_data:
            print(f"❌ Error in DOGE data: {doge_data['error']}")
        else:
            print(f"✅ DOGE price: {doge_data.get('price', 'N/A')}")
            print(f"✅ DOGE change: {doge_data.get('change_percent', 'N/A')}")

            if 'indicators' in doge_data:
                indicators = doge_data['indicators']
                print(f"✅ Indicators found: {list(indicators.keys())}")

                # Check specific indicators
                for key, value in indicators.items():
                    print(f"  {key}: {value}")
            else:
                print("❌ No indicators in DOGE data")

        # Test detailed indicators directly
        print("\n--- Testing get_doge_detailed_indicators() directly ---")
        detailed = monitor.get_doge_detailed_indicators()
        print(f"Detailed indicators type: {type(detailed)}")
        print(f"Detailed indicators keys: {list(detailed.keys())}")

        for key, value in detailed.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_monitor()