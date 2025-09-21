#!/usr/bin/env python3
"""
Vercel部署专用的API入口文件
"""

import sys
import os
import json
from flask import Flask, render_template, jsonify

# 添加根目录到路径
root_path = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(root_path, 'src')
if root_path not in sys.path:
    sys.path.insert(0, root_path)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 创建Flask应用
app = Flask(__name__,
    template_folder=os.path.join(root_path, 'web', 'templates'),
    static_folder=os.path.join(root_path, 'web', 'static')
)

# 导入必要模块
binance_api = None
try:
    from src.data.binance_api import BinanceAPI
    from src.indicators.boll import BOLL
    from src.indicators.kdj import KDJ
    binance_api = BinanceAPI()
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 导入模块失败: {e}")
    import traceback
    traceback.print_exc()

@app.route('/')
def index():
    """主页面"""
    return render_template('monitor.html')

@app.route('/api/btc-data')
def get_btc_data():
    """获取BTC数据API"""
    try:
        print("🔍 开始获取BTC数据")

        if not binance_api:
            print("❌ binance_api未初始化")
            return jsonify({'error': '服务暂不可用'}), 500

        # 获取基础数据
        print("📡 获取24小时数据")
        ticker_24h = binance_api.get_24hr_ticker('BTCUSDT')
        print(f"📊 获取到数据: {ticker_24h is not None}")

        if not ticker_24h:
            print("❌ 无法获取24h数据")
            return jsonify({'error': '无法获取数据'}), 500

        current_price = float(ticker_24h['lastPrice'])
        price_change_percent = float(ticker_24h['priceChangePercent'])
        high_24h = float(ticker_24h['highPrice'])
        low_24h = float(ticker_24h['lowPrice'])
        amplitude = ((high_24h - low_24h) / low_24h) * 100

        # 获取技术指标
        indicators = {}

        # 4小时指标
        try:
            df_4h = binance_api.get_klines('BTCUSDT', '4h', limit=50)
            if not df_4h.empty:
                boll_4h = BOLL(period=20, std_dev=2)
                kdj_4h = KDJ(k_period=9, d_period=3, j_period=3)

                boll_values_4h = boll_4h.get_latest_values(df_4h)
                kdj_values_4h = kdj_4h.get_latest_values(df_4h)

                indicators['4h'] = {
                    'boll': boll_values_4h,
                    'kdj': kdj_values_4h
                }
        except Exception as e:
            print(f"4小时指标计算失败: {e}")

        # 1小时指标
        try:
            df_1h = binance_api.get_klines('BTCUSDT', '1h', limit=50)
            if not df_1h.empty:
                boll_1h = BOLL(period=20, std_dev=2)
                kdj_1h = KDJ(k_period=9, d_period=3, j_period=3)

                boll_values_1h = boll_1h.get_latest_values(df_1h)
                kdj_values_1h = kdj_1h.get_latest_values(df_1h)

                indicators['1h'] = {
                    'boll': boll_values_1h,
                    'kdj': kdj_values_1h
                }
        except Exception as e:
            print(f"1小时指标计算失败: {e}")

        return jsonify({
            'symbol': 'BTCUSDT',
            'price': current_price,
            'change': price_change_percent,
            'amplitude_24h': round(amplitude, 3),
            'growth_24h': price_change_percent,
            'high_24h': high_24h,
            'low_24h': low_24h,
            'indicators': indicators,
            'timestamp': int(time.time() * 1000)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/doge-data')
def get_doge_data():
    """获取DOGE数据API"""
    try:
        if not binance_api:
            return jsonify({'error': '服务暂不可用'}), 500

        # 获取基础数据
        ticker_24h = binance_api.get_24hr_ticker('DOGEUSDT')

        if not ticker_24h:
            return jsonify({'error': '无法获取数据'}), 500

        current_price = float(ticker_24h['lastPrice'])
        price_change_percent = float(ticker_24h['priceChangePercent'])
        high_24h = float(ticker_24h['highPrice'])
        low_24h = float(ticker_24h['lowPrice'])
        amplitude = ((high_24h - low_24h) / low_24h) * 100

        # 获取技术指标
        indicators = {}

        for timeframe in ['1h', '15m', '1m']:
            try:
                df = binance_api.get_klines('DOGEUSDT', timeframe, limit=50)
                if not df.empty:
                    boll = BOLL(period=20, std_dev=2)
                    kdj = KDJ(k_period=9, d_period=3, j_period=3)

                    boll_values = boll.get_latest_values(df)
                    kdj_values = kdj.get_latest_values(df)

                    indicators[timeframe] = {
                        'boll': boll_values,
                        'kdj': kdj_values
                    }
            except Exception as e:
                print(f"DOGE {timeframe}指标计算失败: {e}")

        return jsonify({
            'symbol': 'DOGEUSDT',
            'price': current_price,
            'change': price_change_percent,
            'amplitude_24h': round(amplitude, 3),
            'growth_24h': price_change_percent,
            'high_24h': high_24h,
            'low_24h': low_24h,
            'indicators': indicators,
            'timestamp': int(time.time() * 1000)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel入口点
import time
if __name__ == '__main__':
    app.run(debug=True)
else:
    # Vercel部署时的入口点
    application = app