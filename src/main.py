#!/usr/bin/env python3
"""
币安量化交易信号生成器 - 主程序
监控BTC/USDT和DOGE/USDT，生成买卖信号
"""

import time
import argparse
from datetime import datetime
from typing import List, Dict

from .data.binance_api import binance_api
from .strategy.doge_signals import doge_signal_generator
from .strategy.btc_monitor import btc_monitor
from .utils.config import config
from .utils.logger import logger


class TradingSignalMonitor:
    """交易信号监控器"""

    def __init__(self):
        self.is_running = False
        self.update_interval = config.get('monitoring.update_interval', 60)
        self.last_signals = []

    def start_monitoring(self):
        """开始监控"""
        self.is_running = True
        logger.info("🚀 交易信号监控启动")
        logger.info(f"监控间隔: {self.update_interval}秒")

        # 测试API连接
        if not binance_api.test_connection():
            logger.error("API连接失败，退出监控")
            return

        try:
            while self.is_running:
                self.check_signals()
                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            logger.info("接收到停止信号，正在退出...")
        except Exception as e:
            logger.error(f"监控过程中发生错误: {str(e)}")
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        logger.info("📴 交易信号监控已停止")

    def check_signals(self):
        """检查交易信号"""
        try:
            # 获取详细计算数据用于日志记录
            btc_data = self.get_btc_calculation_data()
            doge_data = self.get_doge_calculation_data()

            # 记录详细计算过程到日志
            logger.calculation_details(btc_data, doge_data)

            # 检查所有信号
            signals = doge_signal_generator.check_all_signals()

            if signals:
                for signal in signals:
                    self.process_signal(signal)
            else:
                # 显示当前状态（每10次检查显示一次）
                current_time = datetime.now()
                if current_time.minute % 10 == 0:
                    self.show_status()

        except Exception as e:
            logger.error(f"信号检查失败: {str(e)}")

    def get_btc_calculation_data(self) -> dict:
        """获取BTC计算数据"""
        try:
            from .data.binance_api import binance_api
            from .indicators.kdj import KDJ

            # 获取BTC基础数据
            btc_ticker = binance_api.get_24hr_ticker('BTCUSDT')
            if not btc_ticker:
                return {}

            btc_price = float(btc_ticker['lastPrice'])
            btc_stats = binance_api.calculate_24h_stats('BTCUSDT')

            # 获取KDJ数据
            kdj = KDJ()
            btc_4h = binance_api.get_klines('BTCUSDT', '4h', 50)
            btc_1h = binance_api.get_klines('BTCUSDT', '1h', 50)

            kdj_4h = 0
            kdj_1h = 0

            if not btc_4h.empty:
                kdj_4h_values = kdj.get_latest_values(btc_4h)
                kdj_4h = kdj_4h_values.get('KDJ_MAX', 0)

            if not btc_1h.empty:
                kdj_1h_values = kdj.get_latest_values(btc_1h)
                kdj_1h = kdj_1h_values.get('KDJ_MAX', 0)

            # 检查条件
            btc_conditions = btc_monitor.check_all_conditions()

            return {
                'price': btc_price,
                'volatility': btc_stats.get('volatility', 0),
                'change_percent': btc_stats.get('change_percent', 0),
                'kdj_4h': kdj_4h,
                'kdj_1h': kdj_1h,
                'condition_met': btc_conditions['valid']
            }

        except Exception as e:
            logger.error(f"获取BTC计算数据失败: {str(e)}")
            return {}

    def get_doge_calculation_data(self) -> dict:
        """获取DOGE计算数据"""
        try:
            from .data.binance_api import binance_api
            from .indicators.boll import BOLL
            from .indicators.kdj import KDJ

            # 获取DOGE基础数据
            doge_ticker = binance_api.get_24hr_ticker('DOGEUSDT')
            if not doge_ticker:
                return {}

            doge_price = float(doge_ticker['lastPrice'])

            # 获取技术指标数据
            boll = BOLL()
            kdj = KDJ()

            doge_1h = binance_api.get_klines('DOGEUSDT', '1h', 50)
            doge_15m = binance_api.get_klines('DOGEUSDT', '15m', 50)
            doge_1m = binance_api.get_klines('DOGEUSDT', '1m', 50)

            result = {'price': doge_price}

            # 1小时指标
            if not doge_1h.empty:
                boll_1h = boll.get_latest_values(doge_1h)
                kdj_1h = kdj.get_latest_values(doge_1h)

                result['boll_1h'] = boll_1h.get('touch', '无')
                result['kdj_1h'] = kdj_1h.get('KDJ_MAX', 0)

            # 15分钟指标
            if not doge_15m.empty:
                kdj_15m = kdj.get_latest_values(doge_15m)
                result['kdj_15m'] = kdj_15m.get('KDJ_MAX', 0)

            # 1分钟指标
            if not doge_1m.empty:
                kdj_1m = kdj.get_latest_values(doge_1m)
                result['kdj_1m'] = kdj_1m.get('KDJ_MAX', 0)

            return result

        except Exception as e:
            logger.error(f"获取DOGE计算数据失败: {str(e)}")
            return {}

    def process_signal(self, signal: Dict):
        """处理信号"""
        try:
            signal_type = signal.get('type', 'unknown')
            signal_id = signal.get('signal_id', 0)
            symbol = config.get('symbols.doge', 'DOGEUSDT')

            # 生成信号消息
            if signal_type == 'buy':
                logger.signal('Buy', symbol, signal_id)
            elif signal_type == 'sell':
                logger.signal('Sell', symbol, signal_id)

        except Exception as e:
            logger.error(f"处理信号失败: {str(e)}")

    def show_status(self):
        """显示当前状态"""
        try:
            # 获取BTC状态
            btc_status = btc_monitor.get_status_summary()
            logger.info(f"📊 {btc_status}")

            # 获取DOGE当前价格
            btc_symbol = config.get('symbols.btc', 'BTCUSDT')
            doge_symbol = config.get('symbols.doge', 'DOGEUSDT')

            btc_stats = binance_api.calculate_24h_stats(btc_symbol)
            doge_ticker = binance_api.get_24hr_ticker(doge_symbol)

            if doge_ticker:
                doge_price = doge_ticker.get('lastPrice', 0)
                doge_change = doge_ticker.get('priceChangePercent', 0)
                logger.info(f"💰 DOGE价格: ${doge_price:.6f} ({doge_change:+.2f}%)")

        except Exception as e:
            logger.debug(f"状态显示失败: {str(e)}")

    def test_mode(self):
        """测试模式 - 运行一次检查"""
        logger.info("🧪 测试模式运行")

        # 测试API连接
        if not binance_api.test_connection():
            logger.error("API连接失败")
            return False

        try:
            # 检查BTC条件
            btc_status = btc_monitor.get_status_summary()
            logger.info(f"BTC状态: {btc_status}")

            # 检查DOGE信号
            signals = doge_signal_generator.check_all_signals()

            if signals:
                logger.info(f"检测到 {len(signals)} 个信号:")
                for signal in signals:
                    signal_type = signal.get('type', 'unknown')
                    signal_id = signal.get('signal_id', 0)
                    logger.info(f"  - {signal_type.upper()} Signal {signal_id}")
            else:
                logger.info("当前无信号触发")

            # 显示当前价格
            self.show_status()

            logger.info("✅ 测试模式完成")
            return True

        except Exception as e:
            logger.error(f"测试模式失败: {str(e)}")
            return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='币安量化交易信号生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                 # 启动持续监控
  python main.py --test          # 测试模式（运行一次）
  python main.py --interval 30   # 设置30秒检查间隔
        """
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式，运行一次检查后退出'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=None,
        help='监控间隔（秒），默认使用配置文件设置'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )

    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()

    # 创建监控器
    monitor = TradingSignalMonitor()

    # 设置更新间隔
    if args.interval:
        monitor.update_interval = args.interval

    try:
        if args.test:
            # 测试模式
            success = monitor.test_mode()
            exit(0 if success else 1)
        else:
            # 持续监控模式
            logger.info("启动交易信号监控...")
            logger.info("按 Ctrl+C 停止监控")
            monitor.start_monitoring()

    except Exception as e:
        logger.error(f"程序运行失败: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()