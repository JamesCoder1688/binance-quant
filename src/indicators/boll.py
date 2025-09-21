import pandas as pd
import numpy as np
from typing import Tuple, Dict

from ..utils.config import config


class BOLL:
    """布林带指标计算器 (BOLL, 20, 2)"""

    def __init__(self, period: int = None, std_dev: float = None):
        boll_config = config.get_indicator_config('boll')
        self.period = period or boll_config.get('period', 20)
        self.std_dev = std_dev or boll_config.get('std_dev', 2)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算布林带指标

        Args:
            df: 包含OHLCV数据的DataFrame

        Returns:
            包含MB、UP、DN的DataFrame
        """
        if df.empty or len(df) < self.period:
            return pd.DataFrame()

        try:
            # 复制原数据框
            result = df.copy()

            # 中轨 MB = 收盘价20周期简单移动平均线
            result['MB'] = result['close'].rolling(window=self.period).mean()

            # 标准差
            std = result['close'].rolling(window=self.period).std()

            # 上轨 UP = MB + 2 × 标准差
            result['UP'] = result['MB'] + (self.std_dev * std)

            # 下轨 DN = MB - 2 × 标准差
            result['DN'] = result['MB'] - (self.std_dev * std)

            # 去除NaN值
            result = result.dropna()

            return result

        except Exception as e:
            raise ValueError(f"BOLL计算失败: {str(e)}")

    def check_touch_condition(self, high: float, low: float, close: float, mb: float, up: float, dn: float) -> str:
        """
        检查价格触及布林带的条件 - 影线法

        Args:
            high: 最高价
            low: 最低价
            close: 收盘价
            mb: 中轨值
            up: 上轨值
            dn: 下轨值

        Returns:
            'UP': 触及上轨, 'DN': 触及下轨, 'MB': 接近中轨, '': 无触及
        """
        try:
            # 容差阈值（0.1%）
            tolerance = 0.001

            # 触及上轨：最高价 >= 上轨
            if high >= up:
                return 'UP'

            # 触及下轨：最低价 <= 下轨
            if low <= dn:
                return 'DN'

            # 接近中轨：收盘价在中轨附近 ±0.1%
            mb_range = mb * tolerance
            if abs(close - mb) <= mb_range:
                return 'MB'

            return ''

        except Exception as e:
            raise ValueError(f"布林带触及条件检查失败: {str(e)}")

    def get_latest_values(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        获取最新的布林带值

        Returns:
            {'MB': 中轨, 'UP': 上轨, 'DN': 下轨, 'close': 收盘价, 'touch': 触及状态}
        """
        if df.empty:
            return {}

        try:
            boll_df = self.calculate(df)
            if boll_df.empty:
                return {}

            latest = boll_df.iloc[-1]
            current_price = latest['close']

            touch = self.check_touch_condition(
                latest['high'], latest['low'], latest['close'],
                latest['MB'], latest['UP'], latest['DN']
            )

            return {
                'MB': latest['MB'],
                'UP': latest['UP'],
                'DN': latest['DN'],
                'close': current_price,
                'high': latest['high'],
                'low': latest['low'],
                'touch': touch
            }

        except Exception as e:
            raise ValueError(f"获取布林带最新值失败: {str(e)}")


def calculate_boll(df: pd.DataFrame, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
    """便捷函数：计算布林带指标"""
    boll = BOLL(period, std_dev)
    return boll.calculate(df)