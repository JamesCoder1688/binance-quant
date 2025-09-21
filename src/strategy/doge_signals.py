from typing import Dict, List, Optional
import pandas as pd

from ..data.binance_api import binance_api
from ..indicators.boll import BOLL
from ..indicators.kdj import KDJ
from ..strategy.btc_monitor import btc_monitor
from ..utils.config import config
from ..utils.logger import logger


class DOGESignalGenerator:
    """DOGE/USDT买卖信号生成器"""

    def __init__(self):
        self.symbol = config.get('symbols.doge', 'DOGEUSDT')
        strategy_config = config.get_strategy_config()
        doge_thresholds = strategy_config.get('doge_thresholds', {})

        self.oversold_thresholds = doge_thresholds.get('oversold', [10, 15, 20])
        self.overbought_threshold = doge_thresholds.get('overbought', 90)

        self.boll_calculator = BOLL()
        self.kdj_calculator = KDJ()

        # 缓存最近的数据以提高性能
        self._data_cache = {}

    def _get_market_data(self, interval: str, limit: int = 100) -> pd.DataFrame:
        """获取市场数据（带缓存）"""
        cache_key = f"{self.symbol}_{interval}"

        try:
            # 获取K线数据
            df = binance_api.get_klines(self.symbol, interval, limit)

            if not df.empty:
                self._data_cache[cache_key] = df

            return df

        except Exception as e:
            logger.error(f"获取{self.symbol} {interval}数据失败: {str(e)}")
            # 返回缓存数据（如果有）
            return self._data_cache.get(cache_key, pd.DataFrame())

    def _get_indicators(self, df: pd.DataFrame) -> Dict[str, any]:
        """计算技术指标"""
        if df.empty:
            return {'boll': {}, 'kdj': {}}

        try:
            # 计算BOLL指标
            boll_values = self.boll_calculator.get_latest_values(df)

            # 计算KDJ指标
            kdj_values = self.kdj_calculator.get_latest_values(df)

            return {
                'boll': boll_values,
                'kdj': kdj_values
            }

        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return {'boll': {}, 'kdj': {}}

    def check_buy_signal_1(self) -> Dict[str, any]:
        """
        买入信号1：
        - BTC条件满足
        - DOGE 1h触及DN且KDJ<10
        - DOGE 15m触及DN且KDJ<10
        - DOGE 1m KDJ<20
        """
        try:
            # 检查BTC条件
            btc_conditions = btc_monitor.check_all_conditions()
            if not btc_conditions['valid']:
                return {'signal': False, 'reason': 'BTC条件不满足'}

            # 获取DOGE各时间框架数据
            doge_1h = self._get_market_data('1h')
            doge_15m = self._get_market_data('15m')
            doge_1m = self._get_market_data('1m')

            if doge_1h.empty or doge_15m.empty or doge_1m.empty:
                return {'signal': False, 'reason': 'DOGE数据获取失败'}

            # 计算指标
            indicators_1h = self._get_indicators(doge_1h)
            indicators_15m = self._get_indicators(doge_15m)
            indicators_1m = self._get_indicators(doge_1m)

            # 检查条件
            conditions = {
                'btc_ok': True,
                'doge_1h_dn': indicators_1h['boll'].get('touch') == 'DN',
                'doge_1h_kdj': indicators_1h['kdj'].get('KDJ_MAX', 100) < 10,
                'doge_15m_dn': indicators_15m['boll'].get('touch') == 'DN',
                'doge_15m_kdj': indicators_15m['kdj'].get('KDJ_MAX', 100) < 10,
                'doge_1m_kdj': indicators_1m['kdj'].get('KDJ_MAX', 100) < 20
            }

            # 所有条件都要满足
            signal = all(conditions.values())

            result = {
                'signal': signal,
                'signal_id': 1,
                'conditions': conditions,
                'indicators': {
                    '1h': indicators_1h,
                    '15m': indicators_15m,
                    '1m': indicators_1m
                }
            }

            if signal:
                logger.info("🟢 买入信号1触发")

            return result

        except Exception as e:
            logger.error(f"买入信号1检查失败: {str(e)}")
            return {'signal': False, 'reason': f'检查失败: {str(e)}'}

    def check_buy_signal_2(self) -> Dict[str, any]:
        """
        买入信号2：
        - BTC条件满足
        - DOGE 1h触及MB且KDJ<15
        - DOGE 15m触及DN且KDJ<20
        - DOGE 1m KDJ<20
        """
        try:
            # 检查BTC条件
            btc_conditions = btc_monitor.check_all_conditions()
            if not btc_conditions['valid']:
                return {'signal': False, 'reason': 'BTC条件不满足'}

            # 获取DOGE各时间框架数据
            doge_1h = self._get_market_data('1h')
            doge_15m = self._get_market_data('15m')
            doge_1m = self._get_market_data('1m')

            if doge_1h.empty or doge_15m.empty or doge_1m.empty:
                return {'signal': False, 'reason': 'DOGE数据获取失败'}

            # 计算指标
            indicators_1h = self._get_indicators(doge_1h)
            indicators_15m = self._get_indicators(doge_15m)
            indicators_1m = self._get_indicators(doge_1m)

            # 检查条件
            conditions = {
                'btc_ok': True,
                'doge_1h_mb': indicators_1h['boll'].get('touch') == 'MB',
                'doge_1h_kdj': indicators_1h['kdj'].get('KDJ_MAX', 100) < 15,
                'doge_15m_dn': indicators_15m['boll'].get('touch') == 'DN',
                'doge_15m_kdj': indicators_15m['kdj'].get('KDJ_MAX', 100) < 20,
                'doge_1m_kdj': indicators_1m['kdj'].get('KDJ_MAX', 100) < 20
            }

            # 所有条件都要满足
            signal = all(conditions.values())

            result = {
                'signal': signal,
                'signal_id': 2,
                'conditions': conditions,
                'indicators': {
                    '1h': indicators_1h,
                    '15m': indicators_15m,
                    '1m': indicators_1m
                }
            }

            if signal:
                logger.info("🟢 买入信号2触发")

            return result

        except Exception as e:
            logger.error(f"买入信号2检查失败: {str(e)}")
            return {'signal': False, 'reason': f'检查失败: {str(e)}'}

    def check_buy_signal_3(self) -> Dict[str, any]:
        """
        买入信号3：
        - BTC条件满足
        - DOGE 1h触及MB且KDJ<15
        - DOGE 15m触及MB且KDJ<20
        - DOGE 1m KDJ<20
        """
        try:
            # 检查BTC条件
            btc_conditions = btc_monitor.check_all_conditions()
            if not btc_conditions['valid']:
                return {'signal': False, 'reason': 'BTC条件不满足'}

            # 获取DOGE各时间框架数据
            doge_1h = self._get_market_data('1h')
            doge_15m = self._get_market_data('15m')
            doge_1m = self._get_market_data('1m')

            if doge_1h.empty or doge_15m.empty or doge_1m.empty:
                return {'signal': False, 'reason': 'DOGE数据获取失败'}

            # 计算指标
            indicators_1h = self._get_indicators(doge_1h)
            indicators_15m = self._get_indicators(doge_15m)
            indicators_1m = self._get_indicators(doge_1m)

            # 检查条件
            conditions = {
                'btc_ok': True,
                'doge_1h_mb': indicators_1h['boll'].get('touch') == 'MB',
                'doge_1h_kdj': indicators_1h['kdj'].get('KDJ_MAX', 100) < 15,
                'doge_15m_mb': indicators_15m['boll'].get('touch') == 'MB',
                'doge_15m_kdj': indicators_15m['kdj'].get('KDJ_MAX', 100) < 20,
                'doge_1m_kdj': indicators_1m['kdj'].get('KDJ_MAX', 100) < 20
            }

            # 所有条件都要满足
            signal = all(conditions.values())

            result = {
                'signal': signal,
                'signal_id': 3,
                'conditions': conditions,
                'indicators': {
                    '1h': indicators_1h,
                    '15m': indicators_15m,
                    '1m': indicators_1m
                }
            }

            if signal:
                logger.info("🟢 买入信号3触发")

            return result

        except Exception as e:
            logger.error(f"买入信号3检查失败: {str(e)}")
            return {'signal': False, 'reason': f'检查失败: {str(e)}'}

    def check_sell_signals(self) -> List[Dict[str, any]]:
        """检查所有卖出信号"""
        sell_signals = []

        try:
            # 获取DOGE各时间框架数据
            doge_1h = self._get_market_data('1h')
            doge_15m = self._get_market_data('15m')
            doge_1m = self._get_market_data('1m')

            if doge_1h.empty or doge_15m.empty or doge_1m.empty:
                return []

            # 计算指标
            indicators_1h = self._get_indicators(doge_1h)
            indicators_15m = self._get_indicators(doge_15m)
            indicators_1m = self._get_indicators(doge_1m)

            # 卖出信号1: 1h触及UP且KDJ>90, 15m触及MB且1hKDJ>90, 1mKDJ>90
            conditions_1 = {
                'doge_1h_up': indicators_1h['boll'].get('touch') == 'UP',
                'doge_1h_kdj': indicators_1h['kdj'].get('KDJ_MAX', 0) > 90,
                'doge_15m_mb': indicators_15m['boll'].get('touch') == 'MB',
                'doge_1m_kdj': indicators_1m['kdj'].get('KDJ_MAX', 0) > 90
            }
            if all(conditions_1.values()):
                sell_signals.append({
                    'signal': True,
                    'signal_id': 1,
                    'type': 'sell',
                    'conditions': conditions_1
                })

            # 卖出信号2: 1h触及UP且KDJ>90, 15m触及UP且1hKDJ>90, 1mKDJ>90
            conditions_2 = {
                'doge_1h_up': indicators_1h['boll'].get('touch') == 'UP',
                'doge_1h_kdj': indicators_1h['kdj'].get('KDJ_MAX', 0) > 90,
                'doge_15m_up': indicators_15m['boll'].get('touch') == 'UP',
                'doge_1m_kdj': indicators_1m['kdj'].get('KDJ_MAX', 0) > 90
            }
            if all(conditions_2.values()):
                sell_signals.append({
                    'signal': True,
                    'signal_id': 2,
                    'type': 'sell',
                    'conditions': conditions_2
                })

            # 卖出信号3: 1h触及MB且KDJ>90, 15m触及MB且1hKDJ>90, 1mKDJ>90
            conditions_3 = {
                'doge_1h_mb': indicators_1h['boll'].get('touch') == 'MB',
                'doge_1h_kdj': indicators_1h['kdj'].get('KDJ_MAX', 0) > 90,
                'doge_15m_mb': indicators_15m['boll'].get('touch') == 'MB',
                'doge_1m_kdj': indicators_1m['kdj'].get('KDJ_MAX', 0) > 90
            }
            if all(conditions_3.values()):
                sell_signals.append({
                    'signal': True,
                    'signal_id': 3,
                    'type': 'sell',
                    'conditions': conditions_3
                })

            # 卖出信号4: 1h触及MB且KDJ>90, 15m触及UP且1hKDJ>90, 1mKDJ>90
            conditions_4 = {
                'doge_1h_mb': indicators_1h['boll'].get('touch') == 'MB',
                'doge_1h_kdj': indicators_1h['kdj'].get('KDJ_MAX', 0) > 90,
                'doge_15m_up': indicators_15m['boll'].get('touch') == 'UP',
                'doge_1m_kdj': indicators_1m['kdj'].get('KDJ_MAX', 0) > 90
            }
            if all(conditions_4.values()):
                sell_signals.append({
                    'signal': True,
                    'signal_id': 4,
                    'type': 'sell',
                    'conditions': conditions_4
                })

            if sell_signals:
                logger.info(f"🔴 检测到{len(sell_signals)}个卖出信号")

            return sell_signals

        except Exception as e:
            logger.error(f"卖出信号检查失败: {str(e)}")
            return []

    def check_all_signals(self) -> List[Dict[str, any]]:
        """检查所有买卖信号"""
        all_signals = []

        # 检查买入信号
        buy_signals = [
            self.check_buy_signal_1(),
            self.check_buy_signal_2(),
            self.check_buy_signal_3()
        ]

        for signal in buy_signals:
            if signal.get('signal', False):
                signal['type'] = 'buy'
                all_signals.append(signal)

        # 检查卖出信号
        sell_signals = self.check_sell_signals()
        all_signals.extend(sell_signals)

        return all_signals


# 全局DOGE信号生成器实例
doge_signal_generator = DOGESignalGenerator()