import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

from ..utils.config import config
from ..utils.logger import logger


class BinanceAPI:
    """Binance REST API 封装类"""

    def __init__(self):
        api_config = config.get_api_config()
        self.base_url = api_config.get('base_url', 'https://api.binance.com')
        self.timeout = api_config.get('timeout', 10)
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {endpoint}, 错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"处理API响应失败: {str(e)}")
            raise

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """
        获取K线数据

        Args:
            symbol: 交易对，如 'BTCUSDT'
            interval: 时间间隔，如 '1h', '15m', '1m'
            limit: 获取数量，最大1000

        Returns:
            包含OHLCV数据的DataFrame
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': min(limit, 1000)
        }

        try:
            data = self._make_request('/api/v3/klines', params)

            # 转换为DataFrame
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'count', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])

            # 数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 时间转换
            df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # 只保留需要的列
            df = df[['open', 'high', 'low', 'close', 'volume']]

            logger.debug(f"获取{symbol} {interval}数据: {len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"获取K线数据失败: {symbol} {interval}, 错误: {str(e)}")
            return pd.DataFrame()

    def get_24hr_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取24小时价格统计

        Args:
            symbol: 交易对

        Returns:
            24小时统计数据
        """
        params = {'symbol': symbol}

        try:
            data = self._make_request('/api/v3/ticker/24hr', params)

            # 转换数值类型
            numeric_fields = ['priceChange', 'priceChangePercent', 'weightedAvgPrice',
                            'prevClosePrice', 'lastPrice', 'bidPrice', 'askPrice',
                            'openPrice', 'highPrice', 'lowPrice', 'volume', 'count']

            for field in numeric_fields:
                if field in data:
                    data[field] = float(data[field])

            return data

        except Exception as e:
            logger.error(f"获取24小时统计失败: {symbol}, 错误: {str(e)}")
            return {}

    def calculate_24h_stats(self, symbol: str) -> Dict[str, float]:
        """
        计算24小时振幅和涨幅
        振幅 = (最高价 - 最低价) / 最低价

        Returns:
            {'volatility': 振幅, 'change_percent': 涨幅百分比}
        """
        try:
            ticker = self.get_24hr_ticker(symbol)
            if not ticker:
                return {'volatility': 0.0, 'change_percent': 0.0}

            high_price = ticker.get('highPrice', 0)
            low_price = ticker.get('lowPrice', 0)
            open_price = ticker.get('openPrice', 0)

            # 计算24小时振幅 = (最高价 - 最低价) / 最低价
            volatility = 0.0
            if low_price > 0:
                volatility = (high_price - low_price) / low_price

            # 涨幅百分比
            change_percent = ticker.get('priceChangePercent', 0.0) / 100.0

            return {
                'volatility': volatility,
                'change_percent': change_percent
            }

        except Exception as e:
            logger.error(f"计算24小时统计失败: {symbol}, 错误: {str(e)}")
            return {'volatility': 0.0, 'change_percent': 0.0}

    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            self._make_request('/api/v3/ping')
            logger.info("Binance API连接正常")
            return True
        except Exception as e:
            logger.error(f"Binance API连接失败: {str(e)}")
            return False


# 全局API实例
binance_api = BinanceAPI()