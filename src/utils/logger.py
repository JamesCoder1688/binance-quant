import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import config


class TradingLogger:
    """交易信号日志记录器"""

    def __init__(self, name: str = "binance_quant"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """设置日志记录器"""
        log_config = config.get_logging_config()
        level = getattr(logging, log_config.get('level', 'INFO'))
        self.logger.setLevel(level)

        # 清除现有处理器
        self.logger.handlers.clear()

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # 文件处理器
        log_file = log_config.get('file', 'logs/trading_signals.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)

    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)

    def signal(self, signal_type: str, symbol: str, signal_id: int, details: Optional[str] = None):
        """记录交易信号"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        signal_msg = f"{signal_type} Signal {signal_id}: {symbol}"

        if details:
            signal_msg += f" | {details}"

        self.logger.info(signal_msg)

        # 控制台高亮显示信号
        if config.get('monitoring.console_output', True):
            print(f"\n🚨 [{timestamp}] {signal_msg}\n")

    def calculation_details(self, btc_data: dict, doge_data: dict = None):
        """记录详细计算过程"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # BTC计算详情
        btc_msg = f"BTC计算: 价格${btc_data.get('price', 0):,.2f}, "
        btc_msg += f"振幅{btc_data.get('volatility', 0)*100:.2f}%"
        if 'kdj_4h' in btc_data:
            btc_msg += f", 4hKDJ{btc_data['kdj_4h']:.1f}"
        if 'kdj_1h' in btc_data:
            btc_msg += f", 1hKDJ{btc_data['kdj_1h']:.1f}"
        btc_msg += f", 条件{'满足' if btc_data.get('condition_met', False) else '不满足'}"

        self.logger.info(btc_msg)

        # DOGE计算详情（如果提供）
        if doge_data:
            doge_msg = f"DOGE计算: 价格${doge_data.get('price', 0):.6f}"
            if 'boll_1h' in doge_data:
                doge_msg += f", 1hBOLL触及{doge_data['boll_1h']}"
            if 'kdj_1h' in doge_data:
                doge_msg += f", 1hKDJ{doge_data['kdj_1h']:.1f}"
            if 'kdj_15m' in doge_data:
                doge_msg += f", 15mKDJ{doge_data['kdj_15m']:.1f}"
            if 'kdj_1m' in doge_data:
                doge_msg += f", 1mKDJ{doge_data['kdj_1m']:.1f}"

            self.logger.info(doge_msg)

    def market_status(self, status_data: dict):
        """记录市场状态"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        status_msg = f"市场状态: "
        if 'btc_price' in status_data:
            status_msg += f"BTC=${status_data['btc_price']:,.2f}"
        if 'btc_change' in status_data:
            status_msg += f"({status_data['btc_change']:+.2f}%)"
        if 'doge_price' in status_data:
            status_msg += f", DOGE=${status_data['doge_price']:.6f}"
        if 'doge_change' in status_data:
            status_msg += f"({status_data['doge_change']:+.2f}%)"

        self.logger.info(status_msg)


# 全局日志实例
logger = TradingLogger()