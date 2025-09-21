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

# 直接使用requests，不依赖自定义模块
import requests
import time
import pandas as pd
import numpy as np

print("✅ 使用直接API调用模式")

def calculate_boll(prices, period=20, std_dev=2):
    """计算布林带指标"""
    if len(prices) < period:
        return None, None, None

    prices = np.array(prices)
    ma = np.mean(prices[-period:])
    std = np.std(prices[-period:])

    upper = ma + std_dev * std
    lower = ma - std_dev * std

    return upper, ma, lower

def calculate_kdj(highs, lows, closes, k_period=9, d_period=3, j_period=3):
    """计算KDJ指标"""
    if len(closes) < k_period:
        return None, None, None

    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)

    # 计算最近k_period期间的最高价和最低价
    highest = np.max(highs[-k_period:])
    lowest = np.min(lows[-k_period:])

    if highest == lowest:
        rsv = 50
    else:
        rsv = (closes[-1] - lowest) / (highest - lowest) * 100

    # 简化的KDJ计算
    k = rsv * 0.33 + 50 * 0.67  # 简化的K值
    d = k * 0.33 + 50 * 0.67    # 简化的D值
    j = 3 * k - 2 * d           # J值

    return k, d, j

def get_klines_data(symbol, interval, limit=50):
    """获取K线数据"""
    try:
        response = requests.get(
            'https://api.binance.com/api/v3/klines',
            params={
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # 提取OHLC数据
        opens = [float(x[1]) for x in data]
        highs = [float(x[2]) for x in data]
        lows = [float(x[3]) for x in data]
        closes = [float(x[4]) for x in data]

        return opens, highs, lows, closes
    except Exception as e:
        print(f"获取K线数据失败: {e}")
        return None, None, None, None

@app.route('/')
def index():
    """主页面"""
    return render_template('monitor.html')

@app.route('/api/btc-data')
def get_btc_data():
    """获取BTC数据API"""
    try:
        print("🔍 开始获取BTC数据")

        # 直接调用币安API获取24小时数据
        response = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
            timeout=10
        )
        response.raise_for_status()
        ticker_24h = response.json()
        print("✅ 获取24h数据成功")

        current_price = float(ticker_24h['lastPrice'])
        price_change_percent = float(ticker_24h['priceChangePercent'])
        high_24h = float(ticker_24h['highPrice'])
        low_24h = float(ticker_24h['lowPrice'])
        amplitude = ((high_24h - low_24h) / low_24h) * 100

        # 计算技术指标
        indicators = {}

        # 4小时指标
        opens_4h, highs_4h, lows_4h, closes_4h = get_klines_data('BTCUSDT', '4h', 50)
        if closes_4h:
            boll_up_4h, boll_mb_4h, boll_dn_4h = calculate_boll(closes_4h)
            kdj_k_4h, kdj_d_4h, kdj_j_4h = calculate_kdj(highs_4h, lows_4h, closes_4h)

            indicators['4h'] = {
                'boll': {
                    'UP': boll_up_4h,
                    'MB': boll_mb_4h,
                    'DN': boll_dn_4h
                },
                'kdj': {
                    'K': kdj_k_4h,
                    'D': kdj_d_4h,
                    'J': kdj_j_4h
                }
            }

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
        print(f"❌ BTC数据获取失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/doge-data')
def get_doge_data():
    """获取DOGE数据API"""
    try:
        print("🔍 开始获取DOGE数据")

        # 直接调用币安API获取24小时数据
        response = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr?symbol=DOGEUSDT',
            timeout=10
        )
        response.raise_for_status()
        ticker_24h = response.json()

        current_price = float(ticker_24h['lastPrice'])
        price_change_percent = float(ticker_24h['priceChangePercent'])
        high_24h = float(ticker_24h['highPrice'])
        low_24h = float(ticker_24h['lowPrice'])
        amplitude = ((high_24h - low_24h) / low_24h) * 100

        return jsonify({
            'symbol': 'DOGEUSDT',
            'price': current_price,
            'change': price_change_percent,
            'amplitude_24h': round(amplitude, 3),
            'growth_24h': price_change_percent,
            'high_24h': high_24h,
            'low_24h': low_24h,
            'indicators': {},
            'timestamp': int(time.time() * 1000)
        })

    except Exception as e:
        print(f"❌ DOGE数据获取失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Vercel入口点
if __name__ == '__main__':
    app.run(debug=True)
else:
    # Vercel部署时的入口点
    application = app