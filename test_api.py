#!/usr/bin/env python3
"""
测试API是否能正常工作
"""

import requests
import time
import numpy as np
from flask import Flask, jsonify

app = Flask(__name__)

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
        closes = [float(x[4]) for x in data]
        return closes
    except Exception as e:
        print(f"获取K线数据失败: {e}")
        return None

@app.route('/test')
def test():
    """测试端点"""
    try:
        # 获取BTC价格数据
        response = requests.get(
            'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
            timeout=10
        )
        response.raise_for_status()
        ticker_24h = response.json()

        current_price = float(ticker_24h['lastPrice'])

        # 获取K线数据并计算BOLL
        closes = get_klines_data('BTCUSDT', '1h', 20)
        if closes:
            upper, middle, lower = calculate_boll(closes)
            return jsonify({
                'status': 'success',
                'btc_price': current_price,
                'boll': {
                    'upper': upper,
                    'middle': middle,
                    'lower': lower
                }
            })
        else:
            return jsonify({'status': 'error', 'message': 'Failed to get klines data'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)