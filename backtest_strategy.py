#!/usr/bin/env python3
"""
历史数据回测 - 测试交易策略
从9月12日以来的历史数据测试买卖点
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.binance_api import binance_api
from src.indicators.boll import BOLL
from src.indicators.kdj import KDJ
from src.utils.config import config

class StrategyBacktest:
    """策略回测器"""

    def __init__(self):
        # 初始化技术指标
        self.boll = BOLL()
        self.kdj = KDJ()

        # 策略配置
        strategy_config = config.get_strategy_config()
        btc_conditions = strategy_config.get('btc_conditions', {})

        self.volatility_threshold = btc_conditions.get('volatility_threshold', 0.03)  # 3%
        self.growth_threshold = btc_conditions.get('growth_threshold', 0.01)  # 1%
        self.kdj_threshold = btc_conditions.get('kdj_threshold', 50)  # v3.0新阈值

        # 回测结果
        self.signals = []
        self.btc_conditions_history = []

    def get_historical_data(self, symbol: str, interval: str, days: int = 7) -> pd.DataFrame:
        """获取历史数据"""
        try:
            print(f"获取{symbol} {interval}数据，{days}天历史...")

            # 计算需要多少根K线
            intervals_per_day = {
                '1m': 1440,
                '15m': 96,
                '1h': 24,
                '4h': 6,
                '1d': 1
            }

            limit = min(1000, intervals_per_day.get(interval, 24) * days + 100)

            df = binance_api.get_klines(symbol, interval, limit)

            if not df.empty:
                print(f"  成功获取{len(df)}条{symbol} {interval}数据")
            else:
                print(f"  ⚠️ {symbol} {interval}数据获取失败")

            return df

        except Exception as e:
            print(f"获取{symbol} {interval}历史数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_24h_stats(self, df_1h: pd.DataFrame, current_time: pd.Timestamp) -> Dict:
        """计算24小时统计数据"""
        try:
            # 获取当前时间前24小时的数据
            start_time = current_time - timedelta(hours=24)
            recent_data = df_1h[df_1h.index >= start_time].copy()

            if len(recent_data) < 20:  # 至少需要20小时数据
                return {'volatility': 0, 'change_percent': 0}

            open_price = recent_data['open'].iloc[0]
            close_price = recent_data['close'].iloc[-1]
            high_price = recent_data['high'].max()
            low_price = recent_data['low'].min()

            # 振幅计算
            volatility = (high_price - low_price) / open_price

            # 涨跌幅计算
            change_percent = (close_price - open_price) / open_price

            return {
                'volatility': volatility,
                'change_percent': change_percent,
                'open_price': open_price,
                'close_price': close_price,
                'high_price': high_price,
                'low_price': low_price
            }

        except Exception as e:
            print(f"计算24小时统计失败: {str(e)}")
            return {'volatility': 0, 'change_percent': 0}

    def check_btc_conditions(self, btc_1h: pd.DataFrame, btc_4h: pd.DataFrame, current_time: pd.Timestamp) -> Dict:
        """检查BTC条件"""
        try:
            # 计算24小时统计
            stats_24h = self.calculate_24h_stats(btc_1h, current_time)
            volatility = stats_24h.get('volatility', 0)
            change_percent = stats_24h.get('change_percent', 0)

            # 24小时条件
            volatility_ok = volatility < self.volatility_threshold
            growth_ok = change_percent > self.growth_threshold
            condition_24h = volatility_ok or growth_ok

            # 获取当前时间点的KDJ
            btc_4h_recent = btc_4h[btc_4h.index <= current_time].tail(50)
            btc_1h_recent = btc_1h[btc_1h.index <= current_time].tail(50)

            kdj_4h_values = self.kdj.get_latest_values(btc_4h_recent)
            kdj_1h_values = self.kdj.get_latest_values(btc_1h_recent)

            kdj_4h = kdj_4h_values.get('KDJ_MAX', 100)
            kdj_1h = kdj_1h_values.get('KDJ_MAX', 100)

            # KDJ条件
            kdj_4h_ok = kdj_4h < self.kdj_threshold
            kdj_1h_ok = kdj_1h < self.kdj_threshold
            kdj_condition = kdj_4h_ok and kdj_1h_ok

            # 最终条件
            btc_valid = condition_24h and kdj_condition

            result = {
                'timestamp': current_time,
                'valid': btc_valid,
                'volatility': volatility,
                'change_percent': change_percent,
                'volatility_ok': volatility_ok,
                'growth_ok': growth_ok,
                'condition_24h': condition_24h,
                'kdj_4h': kdj_4h,
                'kdj_1h': kdj_1h,
                'kdj_4h_ok': kdj_4h_ok,
                'kdj_1h_ok': kdj_1h_ok,
                'kdj_condition': kdj_condition,
                'btc_price': stats_24h.get('close_price', 0)
            }

            return result

        except Exception as e:
            print(f"BTC条件检查失败: {str(e)}")
            return {'timestamp': current_time, 'valid': False}

    def check_doge_signals(self, doge_1h: pd.DataFrame, doge_15m: pd.DataFrame,
                          doge_1m: pd.DataFrame, current_time: pd.Timestamp) -> List[Dict]:
        """检查DOGE买卖信号"""
        signals = []

        try:
            # 获取当前时间点的数据
            doge_1h_recent = doge_1h[doge_1h.index <= current_time].tail(50)
            doge_15m_recent = doge_15m[doge_15m.index <= current_time].tail(50)
            doge_1m_recent = doge_1m[doge_1m.index <= current_time].tail(50)

            if len(doge_1h_recent) < 20 or len(doge_15m_recent) < 20 or len(doge_1m_recent) < 20:
                return signals

            # 计算技术指标
            boll_1h = self.boll.get_latest_values(doge_1h_recent)
            boll_15m = self.boll.get_latest_values(doge_15m_recent)

            kdj_1h = self.kdj.get_latest_values(doge_1h_recent)
            kdj_15m = self.kdj.get_latest_values(doge_15m_recent)
            kdj_1m = self.kdj.get_latest_values(doge_1m_recent)

            doge_price = doge_1h_recent['close'].iloc[-1]

            # 检查买入信号1
            buy_signal_1 = (
                boll_1h.get('touch') == 'DN' and
                kdj_1h.get('KDJ_MAX', 100) < 10 and
                boll_15m.get('touch') == 'DN' and
                kdj_15m.get('KDJ_MAX', 100) < 20 and
                kdj_1m.get('KDJ_MAX', 100) < 20
            )

            if buy_signal_1:
                signals.append({
                    'timestamp': current_time,
                    'type': 'BUY',
                    'signal_id': 1,
                    'price': doge_price,
                    'conditions': {
                        '1h_boll': boll_1h.get('touch'),
                        '1h_kdj': kdj_1h.get('KDJ_MAX', 0),
                        '15m_boll': boll_15m.get('touch'),
                        '15m_kdj': kdj_15m.get('KDJ_MAX', 0),
                        '1m_kdj': kdj_1m.get('KDJ_MAX', 0)
                    }
                })

            # 检查买入信号2
            buy_signal_2 = (
                boll_1h.get('touch') == 'MB' and
                kdj_1h.get('KDJ_MAX', 100) < 15 and
                boll_15m.get('touch') == 'DN' and
                kdj_15m.get('KDJ_MAX', 100) < 20 and
                kdj_1m.get('KDJ_MAX', 100) < 20
            )

            if buy_signal_2:
                signals.append({
                    'timestamp': current_time,
                    'type': 'BUY',
                    'signal_id': 2,
                    'price': doge_price,
                    'conditions': {
                        '1h_boll': boll_1h.get('touch'),
                        '1h_kdj': kdj_1h.get('KDJ_MAX', 0),
                        '15m_boll': boll_15m.get('touch'),
                        '15m_kdj': kdj_15m.get('KDJ_MAX', 0),
                        '1m_kdj': kdj_1m.get('KDJ_MAX', 0)
                    }
                })

            # 检查买入信号3
            buy_signal_3 = (
                boll_1h.get('touch') == 'MB' and
                kdj_1h.get('KDJ_MAX', 100) < 15 and
                boll_15m.get('touch') == 'MB' and
                kdj_15m.get('KDJ_MAX', 100) < 20 and
                kdj_1m.get('KDJ_MAX', 100) < 20
            )

            if buy_signal_3:
                signals.append({
                    'timestamp': current_time,
                    'type': 'BUY',
                    'signal_id': 3,
                    'price': doge_price,
                    'conditions': {
                        '1h_boll': boll_1h.get('touch'),
                        '1h_kdj': kdj_1h.get('KDJ_MAX', 0),
                        '15m_boll': boll_15m.get('touch'),
                        '15m_kdj': kdj_15m.get('KDJ_MAX', 0),
                        '1m_kdj': kdj_1m.get('KDJ_MAX', 0)
                    }
                })

            # 检查卖出信号1-4
            sell_signals = self.check_sell_signals(boll_1h, boll_15m, kdj_1h, kdj_15m, kdj_1m, doge_price, current_time)
            signals.extend(sell_signals)

        except Exception as e:
            print(f"DOGE信号检查失败: {str(e)}")

        return signals

    def check_sell_signals(self, boll_1h: Dict, boll_15m: Dict, kdj_1h: Dict,
                          kdj_15m: Dict, kdj_1m: Dict, doge_price: float, current_time: pd.Timestamp) -> List[Dict]:
        """检查卖出信号"""
        signals = []

        # 卖出信号1
        sell_signal_1 = (
            boll_1h.get('touch') == 'UP' and
            kdj_1h.get('KDJ_MAX', 0) > 90 and
            boll_15m.get('touch') == 'MB' and
            kdj_1h.get('KDJ_MAX', 0) > 90 and
            kdj_1m.get('KDJ_MAX', 0) > 90
        )

        if sell_signal_1:
            signals.append({
                'timestamp': current_time,
                'type': 'SELL',
                'signal_id': 1,
                'price': doge_price,
                'conditions': {
                    '1h_boll': boll_1h.get('touch'),
                    '1h_kdj': kdj_1h.get('KDJ_MAX', 0),
                    '15m_boll': boll_15m.get('touch'),
                    '15m_kdj': kdj_15m.get('KDJ_MAX', 0),
                    '1m_kdj': kdj_1m.get('KDJ_MAX', 0)
                }
            })

        # 卖出信号2-4类似逻辑...

        return signals

    def run_backtest(self, days: int = 7) -> Dict:
        """运行回测"""
        print("=" * 80)
        print(f"策略回测 - 最近{days}天历史数据")
        print("=" * 80)

        # 获取历史数据
        print("\n获取历史数据...")
        btc_4h = self.get_historical_data('BTCUSDT', '4h', days)
        btc_1h = self.get_historical_data('BTCUSDT', '1h', days)
        doge_1h = self.get_historical_data('DOGEUSDT', '1h', days)
        doge_15m = self.get_historical_data('DOGEUSDT', '15m', days)
        doge_1m = self.get_historical_data('DOGEUSDT', '1m', days)

        if any(df.empty for df in [btc_4h, btc_1h, doge_1h, doge_15m, doge_1m]):
            print("❌ 历史数据获取失败")
            return {'signals': [], 'btc_conditions': []}

        print(f"\n🔍 开始回测分析...")

        # 获取分析时间点（每小时一次）
        start_time = datetime.now() - timedelta(days=days)
        end_time = datetime.now() - timedelta(hours=1)  # 不包括最近1小时

        current_time = start_time
        total_checks = 0
        btc_valid_count = 0

        while current_time <= end_time:
            total_checks += 1

            # 检查BTC条件
            btc_condition = self.check_btc_conditions(btc_1h, btc_4h, current_time)
            self.btc_conditions_history.append(btc_condition)

            if btc_condition.get('valid', False):
                btc_valid_count += 1
                print(f"✅ {current_time.strftime('%m-%d %H:%M')} BTC条件满足，检查DOGE信号...")

                # 检查DOGE信号
                doge_signals = self.check_doge_signals(doge_1h, doge_15m, doge_1m, current_time)

                for signal in doge_signals:
                    self.signals.append(signal)
                    signal_type = signal['type']
                    signal_id = signal['signal_id']
                    price = signal['price']
                    print(f"🚨 {signal_type} Signal {signal_id}: ${price:.6f}")

            # 下一个小时
            current_time += timedelta(hours=1)

        # 生成回测报告
        return self.generate_report(total_checks, btc_valid_count)

    def generate_report(self, total_checks: int, btc_valid_count: int) -> Dict:
        """生成回测报告"""
        print("\n" + "=" * 80)
        print("📈 回测报告")
        print("=" * 80)

        buy_signals = [s for s in self.signals if s['type'] == 'BUY']
        sell_signals = [s for s in self.signals if s['type'] == 'SELL']

        print(f"📊 总检查次数: {total_checks}")
        print(f"✅ BTC条件满足次数: {btc_valid_count} ({btc_valid_count/total_checks*100:.1f}%)")
        print(f"🟢 买入信号总数: {len(buy_signals)}")
        print(f"🔴 卖出信号总数: {len(sell_signals)}")

        if buy_signals:
            print(f"\n🟢 买入信号详情:")
            for signal in buy_signals:
                timestamp = signal['timestamp'].strftime('%m-%d %H:%M')
                signal_id = signal['signal_id']
                price = signal['price']
                print(f"  {timestamp} - 买入信号{signal_id}: ${price:.6f}")

                # 显示触发条件
                conditions = signal['conditions']
                print(f"    条件: 1h布林{conditions['1h_boll']} KDJ{conditions['1h_kdj']:.1f}, "
                      f"15m布林{conditions['15m_boll']} KDJ{conditions['15m_kdj']:.1f}, "
                      f"1m KDJ{conditions['1m_kdj']:.1f}")

        if sell_signals:
            print(f"\n🔴 卖出信号详情:")
            for signal in sell_signals:
                timestamp = signal['timestamp'].strftime('%m-%d %H:%M')
                signal_id = signal['signal_id']
                price = signal['price']
                print(f"  {timestamp} - 卖出信号{signal_id}: ${price:.6f}")

        # BTC条件统计
        if self.btc_conditions_history:
            avg_volatility = sum(c.get('volatility', 0) for c in self.btc_conditions_history) / len(self.btc_conditions_history)
            avg_change = sum(c.get('change_percent', 0) for c in self.btc_conditions_history) / len(self.btc_conditions_history)
            avg_kdj_4h = sum(c.get('kdj_4h', 0) for c in self.btc_conditions_history) / len(self.btc_conditions_history)
            avg_kdj_1h = sum(c.get('kdj_1h', 0) for c in self.btc_conditions_history) / len(self.btc_conditions_history)

            print(f"\n📊 BTC条件统计:")
            print(f"  平均振幅: {avg_volatility*100:.2f}%")
            print(f"  平均涨跌: {avg_change*100:.2f}%")
            print(f"  平均4h KDJ: {avg_kdj_4h:.1f}")
            print(f"  平均1h KDJ: {avg_kdj_1h:.1f}")

        return {
            'signals': self.signals,
            'btc_conditions': self.btc_conditions_history,
            'summary': {
                'total_checks': total_checks,
                'btc_valid_count': btc_valid_count,
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals)
            }
        }

def main():
    """主函数"""
    try:
        backtest = StrategyBacktest()

        print("策略回测工具")
        print("测试从9月12日以来的历史数据")

        # 计算从9月12日到现在的天数
        start_date = datetime(2024, 9, 12)
        current_date = datetime.now()
        days_since = (current_date - start_date).days

        print(f"回测期间: 9月12日至今 ({days_since}天)")

        # 运行回测
        result = backtest.run_backtest(days=days_since)

        print(f"\n✅ 回测完成！")
        print(f"发现 {len(result['signals'])} 个交易信号")

    except Exception as e:
        print(f"回测失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()