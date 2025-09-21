from typing import Dict
import pandas as pd

from ..data.binance_api import binance_api
from ..indicators.kdj import KDJ
from ..utils.config import config
from ..utils.logger import logger


class BTCMonitor:
    """BTC/USDT监控条件判断器"""

    def __init__(self):
        self.symbol = config.get('symbols.btc', 'BTCUSDT')
        strategy_config = config.get_strategy_config()
        btc_conditions = strategy_config.get('btc_conditions', {})

        self.volatility_threshold = btc_conditions.get('volatility_threshold', 0.03)  # 3%
        self.growth_threshold = btc_conditions.get('growth_threshold', 0.01)  # 1%
        self.kdj_threshold = btc_conditions.get('kdj_threshold', 20)

        self.kdj_calculator = KDJ()

    def check_24h_conditions(self) -> Dict[str, any]:
        """
        检查BTC 24小时条件
        - 24小时振幅 < 3% 或 24小时涨幅 > 1%

        Returns:
            {
                'valid': bool,
                'volatility': float,
                'change_percent': float,
                'volatility_ok': bool,
                'growth_ok': bool
            }
        """
        try:
            # 获取24小时统计数据
            stats = binance_api.calculate_24h_stats(self.symbol)
            volatility = stats.get('volatility', 0.0)
            change_percent = stats.get('change_percent', 0.0)

            # 检查条件
            volatility_ok = volatility < self.volatility_threshold
            growth_ok = change_percent > self.growth_threshold

            # 满足任一条件即可
            valid = volatility_ok or growth_ok

            result = {
                'valid': valid,
                'volatility': volatility,
                'change_percent': change_percent,
                'volatility_ok': volatility_ok,
                'growth_ok': growth_ok
            }

            logger.debug(f"BTC 24小时条件检查: {result}")
            return result

        except Exception as e:
            logger.error(f"BTC 24小时条件检查失败: {str(e)}")
            return {
                'valid': False,
                'volatility': 0.0,
                'change_percent': 0.0,
                'volatility_ok': False,
                'growth_ok': False
            }

    def check_kdj_conditions(self) -> Dict[str, any]:
        """
        检查BTC KDJ条件
        - 4小时KDJ < 50 且 1小时KDJ < 50

        Returns:
            {
                'valid': bool,
                'kdj_4h': float,
                'kdj_1h': float,
                'kdj_4h_ok': bool,
                'kdj_1h_ok': bool
            }
        """
        try:
            # 获取4小时KDJ
            klines_4h = binance_api.get_klines(self.symbol, '4h', 100)
            kdj_4h_values = self.kdj_calculator.get_latest_values(klines_4h)
            kdj_4h = kdj_4h_values.get('KDJ_MAX', 0.0)

            # 获取1小时KDJ
            klines_1h = binance_api.get_klines(self.symbol, '1h', 100)
            kdj_1h_values = self.kdj_calculator.get_latest_values(klines_1h)
            kdj_1h = kdj_1h_values.get('KDJ_MAX', 0.0)

            # 检查条件
            kdj_4h_ok = kdj_4h < self.kdj_threshold
            kdj_1h_ok = kdj_1h < self.kdj_threshold

            # 两个条件都要满足
            valid = kdj_4h_ok and kdj_1h_ok

            result = {
                'valid': valid,
                'kdj_4h': kdj_4h,
                'kdj_1h': kdj_1h,
                'kdj_4h_ok': kdj_4h_ok,
                'kdj_1h_ok': kdj_1h_ok
            }

            logger.debug(f"BTC KDJ条件检查: {result}")
            return result

        except Exception as e:
            logger.error(f"BTC KDJ条件检查失败: {str(e)}")
            return {
                'valid': False,
                'kdj_4h': 0.0,
                'kdj_1h': 0.0,
                'kdj_4h_ok': False,
                'kdj_1h_ok': False
            }

    def check_all_conditions(self) -> Dict[str, any]:
        """
        检查所有BTC监控条件

        Returns:
            {
                'valid': bool,
                '24h_conditions': dict,
                'kdj_conditions': dict
            }
        """
        try:
            # 检查24小时条件
            conditions_24h = self.check_24h_conditions()

            # 检查KDJ条件
            kdj_conditions = self.check_kdj_conditions()

            # 所有条件都要满足
            valid = conditions_24h['valid'] and kdj_conditions['valid']

            result = {
                'valid': valid,
                '24h_conditions': conditions_24h,
                'kdj_conditions': kdj_conditions
            }

            if valid:
                logger.info(f"✅ BTC监控条件全部满足")
            else:
                logger.debug(f"❌ BTC监控条件不满足")

            return result

        except Exception as e:
            logger.error(f"BTC监控条件检查失败: {str(e)}")
            return {
                'valid': False,
                '24h_conditions': {},
                'kdj_conditions': {}
            }

    def get_status_summary(self) -> str:
        """获取BTC监控状态摘要"""
        try:
            conditions = self.check_all_conditions()

            if not conditions['valid']:
                return "BTC条件不满足"

            h24 = conditions['24h_conditions']
            kdj = conditions['kdj_conditions']

            summary_parts = []

            # 24小时条件描述
            if h24['volatility_ok']:
                summary_parts.append(f"振幅{h24['volatility']:.2%}<3%")
            if h24['growth_ok']:
                summary_parts.append(f"涨幅{h24['change_percent']:.2%}>1%")

            # KDJ条件描述
            summary_parts.append(f"4hKDJ{kdj['kdj_4h']:.1f}<50")
            summary_parts.append(f"1hKDJ{kdj['kdj_1h']:.1f}<50")

            return "BTC条件满足: " + ", ".join(summary_parts)

        except Exception as e:
            return f"BTC状态获取失败: {str(e)}"


# 全局BTC监控实例
btc_monitor = BTCMonitor()