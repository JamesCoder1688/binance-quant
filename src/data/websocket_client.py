import json
import websocket
import threading
from typing import Dict, Callable, Any
from datetime import datetime

from ..utils.config import config
from ..utils.logger import logger


class BinanceWebSocket:
    """Binance WebSocket实时数据客户端"""

    def __init__(self):
        ws_config = config.get_api_config()
        self.ws_url = ws_config.get('ws_url', 'wss://stream.binance.com:9443/stream')
        self.ws = None
        self.subscriptions = {}
        self.callbacks = {}
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    def on_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            stream = data.get('stream', '')

            if stream in self.callbacks:
                callback = self.callbacks[stream]
                if callback:
                    callback(data['data'])

        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {str(e)}")

    def on_error(self, ws, error):
        """处理WebSocket错误"""
        logger.error(f"WebSocket错误: {str(error)}")

    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket连接关闭"""
        logger.warning("WebSocket连接关闭")
        self.is_connected = False

        # 自动重连
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            threading.Timer(5.0, self.connect).start()

    def on_open(self, ws):
        """WebSocket连接建立"""
        logger.info("WebSocket连接已建立")
        self.is_connected = True
        self.reconnect_attempts = 0

        # 重新订阅所有流
        if self.subscriptions:
            self.subscribe_streams(list(self.subscriptions.keys()))

    def connect(self):
        """建立WebSocket连接"""
        try:
            websocket.enableTrace(False)
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )

            # 在新线程中运行
            wst = threading.Thread(target=self.ws.run_forever)
            wst.daemon = True
            wst.start()

        except Exception as e:
            logger.error(f"建立WebSocket连接失败: {str(e)}")

    def subscribe_kline(self, symbol: str, interval: str, callback: Callable):
        """
        订阅K线数据流

        Args:
            symbol: 交易对，如 'btcusdt'
            interval: 时间间隔，如 '1h', '15m', '1m'
            callback: 回调函数
        """
        stream = f"{symbol.lower()}@kline_{interval}"
        self.subscriptions[stream] = True
        self.callbacks[stream] = callback

        if self.is_connected:
            self.subscribe_streams([stream])

        logger.info(f"订阅K线数据流: {stream}")

    def subscribe_streams(self, streams: list):
        """订阅多个数据流"""
        if not self.ws or not self.is_connected:
            return

        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": int(datetime.now().timestamp())
        }

        try:
            self.ws.send(json.dumps(subscribe_msg))
            logger.debug(f"订阅数据流: {streams}")
        except Exception as e:
            logger.error(f"订阅数据流失败: {str(e)}")

    def unsubscribe_stream(self, stream: str):
        """取消订阅数据流"""
        if stream in self.subscriptions:
            del self.subscriptions[stream]
            del self.callbacks[stream]

        if not self.ws or not self.is_connected:
            return

        unsubscribe_msg = {
            "method": "UNSUBSCRIBE",
            "params": [stream],
            "id": int(datetime.now().timestamp())
        }

        try:
            self.ws.send(json.dumps(unsubscribe_msg))
            logger.info(f"取消订阅数据流: {stream}")
        except Exception as e:
            logger.error(f"取消订阅失败: {str(e)}")

    def close(self):
        """关闭WebSocket连接"""
        if self.ws:
            self.ws.close()
            self.is_connected = False
            logger.info("WebSocket连接已关闭")


# 全局WebSocket实例
websocket_client = BinanceWebSocket()