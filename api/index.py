#!/usr/bin/env python3
"""
Vercel部署专用的API入口文件
"""

from flask import Flask, render_template, jsonify
import requests
import json
import time
import math

# 创建Flask应用
app = Flask(__name__)

def calculate_simple_boll(prices, period=20):
    """简化的布林带计算"""
    if len(prices) < period:
        return None, None, None

    # 计算均值
    recent_prices = prices[-period:]
    ma = sum(recent_prices) / len(recent_prices)

    # 计算标准差
    variance = sum((x - ma) ** 2 for x in recent_prices) / len(recent_prices)
    std = math.sqrt(variance)

    upper = ma + 2 * std
    lower = ma - 2 * std

    return upper, ma, lower

def calculate_simple_kdj(highs, lows, closes, period=9):
    """简化的KDJ计算"""
    if len(closes) < period:
        return None, None, None

    # 获取最近期间的数据
    recent_highs = highs[-period:]
    recent_lows = lows[-period:]
    current_close = closes[-1]

    highest = max(recent_highs)
    lowest = min(recent_lows)

    if highest == lowest:
        rsv = 50
    else:
        rsv = (current_close - lowest) / (highest - lowest) * 100

    # 简化的KDJ
    k = rsv * 0.33 + 50 * 0.67
    d = k * 0.33 + 50 * 0.67
    j = 3 * k - 2 * d

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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>币安量化监控</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 20px; background: #f0f0f0; margin: 20px 0; border-radius: 5px; }
            .price { font-size: 24px; font-weight: bold; color: #333; }
            .positive { color: green; }
            .negative { color: red; }
            .indicators { margin: 20px 0; }
            .indicator-row { display: flex; justify-content: space-between; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 币安量化交易监控</h1>

            <div class="status">
                <h2>📊 BTC/USDT</h2>
                <div id="btc-data">加载中...</div>
            </div>

            <div class="status">
                <h2>💎 DOGE/USDT</h2>
                <div id="doge-data">加载中...</div>
            </div>
        </div>

        <script>
            async function fetchData() {
                try {
                    const btcResponse = await fetch('/api/btc-data');
                    const btcData = await btcResponse.json();

                    if (btcData.error) {
                        document.getElementById('btc-data').innerHTML = '❌ 错误: ' + btcData.error;
                    } else {
                        document.getElementById('btc-data').innerHTML = `
                            <div class="price">$${btcData.price.toLocaleString()}</div>
                            <div class="${btcData.change >= 0 ? 'positive' : 'negative'}">
                                ${btcData.change >= 0 ? '+' : ''}${btcData.change.toFixed(2)}%
                            </div>
                            <div class="indicators">
                                <h3>4小时指标</h3>
                                ${btcData.indicators['4h'] ? `
                                    <div>BOLL: ${btcData.indicators['4h'].boll.UP.toFixed(2)} / ${btcData.indicators['4h'].boll.MB.toFixed(2)} / ${btcData.indicators['4h'].boll.DN.toFixed(2)}</div>
                                    <div>KDJ: ${btcData.indicators['4h'].kdj.K.toFixed(1)} / ${btcData.indicators['4h'].kdj.D.toFixed(1)} / ${btcData.indicators['4h'].kdj.J.toFixed(1)}</div>
                                ` : ''}
                            </div>
                        `;
                    }
                } catch (error) {
                    document.getElementById('btc-data').innerHTML = '❌ 网络错误: ' + error.message;
                }

                try {
                    const dogeResponse = await fetch('/api/doge-data');
                    const dogeData = await dogeResponse.json();

                    if (dogeData.error) {
                        document.getElementById('doge-data').innerHTML = '❌ 错误: ' + dogeData.error;
                    } else {
                        document.getElementById('doge-data').innerHTML = `
                            <div class="price">$${dogeData.price.toFixed(6)}</div>
                            <div class="${dogeData.change >= 0 ? 'positive' : 'negative'}">
                                ${dogeData.change >= 0 ? '+' : ''}${dogeData.change.toFixed(2)}%
                            </div>
                        `;
                    }
                } catch (error) {
                    document.getElementById('doge-data').innerHTML = '❌ 网络错误: ' + error.message;
                }
            }

            // 初始加载
            fetchData();

            // 每3秒刷新
            setInterval(fetchData, 3000);
        </script>
    </body>
    </html>
    """

@app.route('/api/btc-data')
def get_btc_data():
    """获取BTC数据API"""
    try:
        print("🔍 开始获取BTC数据")

        # 获取24小时数据
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
            boll_up_4h, boll_mb_4h, boll_dn_4h = calculate_simple_boll(closes_4h)
            kdj_k_4h, kdj_d_4h, kdj_j_4h = calculate_simple_kdj(highs_4h, lows_4h, closes_4h)

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

        # 获取24小时数据
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