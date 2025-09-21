import pandas as pd
import numpy as np
from typing import Dict

from ..utils.config import config


class KDJ:
    """KDJ随机指标计算器 (9, 3, 3)"""

    def __init__(self, k_period: int = None, k_smooth: int = None, d_smooth: int = None):
        kdj_config = config.get_indicator_config('kdj')
        self.k_period = k_period or kdj_config.get('k_period', 9)
        self.k_smooth = k_smooth or kdj_config.get('k_smooth', 3)
        self.d_smooth = d_smooth or kdj_config.get('d_smooth', 3)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算KDJ指标

        Args:
            df: 包含OHLCV数据的DataFrame

        Returns:
            包含K、D、J值的DataFrame
        """
        if df.empty or len(df) < self.k_period:
            return pd.DataFrame()

        try:
            # 复制原数据框
            result = df.copy()

            # 计算最近N期的最高价和最低价
            low_min = result['low'].rolling(window=self.k_period).min()
            high_max = result['high'].rolling(window=self.k_period).max()

            # RSV = (收盘价 - 最近9根最低价) / (最近9根最高价 - 最近9根最低价) × 100
            result['RSV'] = ((result['close'] - low_min) / (high_max - low_min)) * 100

            # 处理除零情况
            result['RSV'] = result['RSV'].fillna(50)  # 默认值50

            # K值计算：K = 2/3 × K前值 + 1/3 × RSV（初始值50）
            result['K'] = 0.0
            k_alpha = 1.0 / self.k_smooth
            prev_k = 50.0  # 初始K值

            for i in range(len(result)):
                if pd.isna(result['RSV'].iloc[i]):
                    result.loc[result.index[i], 'K'] = prev_k
                else:
                    current_k = (1 - k_alpha) * prev_k + k_alpha * result['RSV'].iloc[i]
                    result.loc[result.index[i], 'K'] = current_k
                    prev_k = current_k

            # D值计算：D = 2/3 × D前值 + 1/3 × K（初始值50）
            result['D'] = 0.0
            d_alpha = 1.0 / self.d_smooth
            prev_d = 50.0  # 初始D值

            for i in range(len(result)):
                current_d = (1 - d_alpha) * prev_d + d_alpha * result['K'].iloc[i]
                result.loc[result.index[i], 'D'] = current_d
                prev_d = current_d

            # J值计算：J = 3K - 2D
            result['J'] = 3 * result['K'] - 2 * result['D']

            # 计算判断值：max(K, D, J)
            result['KDJ_MAX'] = result[['K', 'D', 'J']].max(axis=1)

            # 去除前面无效的数据
            result = result.iloc[self.k_period-1:].copy()

            return result

        except Exception as e:
            raise ValueError(f"KDJ计算失败: {str(e)}")

    def get_latest_values(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        获取最新的KDJ值

        Returns:
            {'K': K值, 'D': D值, 'J': J值, 'KDJ_MAX': 判断值}
        """
        if df.empty:
            return {}

        try:
            kdj_df = self.calculate(df)
            if kdj_df.empty:
                return {}

            latest = kdj_df.iloc[-1]

            return {
                'K': latest['K'],
                'D': latest['D'],
                'J': latest['J'],
                'KDJ_MAX': latest['KDJ_MAX']
            }

        except Exception as e:
            raise ValueError(f"获取KDJ最新值失败: {str(e)}")

    def check_oversold(self, kdj_max: float, threshold: float = 20) -> bool:
        """
        检查是否超卖

        Args:
            kdj_max: KDJ判断值
            threshold: 超卖阈值

        Returns:
            True: 超卖, False: 非超卖
        """
        return kdj_max < threshold

    def check_overbought(self, kdj_max: float, threshold: float = 90) -> bool:
        """
        检查是否超买

        Args:
            kdj_max: KDJ判断值
            threshold: 超买阈值

        Returns:
            True: 超买, False: 非超买
        """
        return kdj_max > threshold

    def get_signal_status(self, kdj_max: float) -> str:
        """
        获取信号状态

        Returns:
            'OVERSOLD': 超卖, 'OVERBOUGHT': 超买, 'NEUTRAL': 中性
        """
        if self.check_oversold(kdj_max, 20):
            return 'OVERSOLD'
        elif self.check_overbought(kdj_max, 90):
            return 'OVERBOUGHT'
        else:
            return 'NEUTRAL'


def calculate_kdj(df: pd.DataFrame, k_period: int = 9, k_smooth: int = 3, d_smooth: int = 3) -> pd.DataFrame:
    """便捷函数：计算KDJ指标"""
    kdj = KDJ(k_period, k_smooth, d_smooth)
    return kdj.calculate(df)