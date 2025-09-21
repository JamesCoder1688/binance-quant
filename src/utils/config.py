import json
import os
from typing import Dict, Any


class Config:
    """配置管理类"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")
        except json.JSONDecodeError:
            raise ValueError(f"配置文件 {self.config_path} 格式错误")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.get('api', {})

    def get_symbols(self) -> Dict[str, str]:
        """获取交易对配置"""
        return self.get('symbols', {})

    def get_timeframes(self) -> Dict[str, list]:
        """获取时间框架配置"""
        return self.get('timeframes', {})

    def get_indicator_config(self, indicator: str) -> Dict[str, Any]:
        """获取指标配置"""
        return self.get(f'indicators.{indicator}', {})

    def get_strategy_config(self) -> Dict[str, Any]:
        """获取策略配置"""
        return self.get('strategy', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})


# 全局配置实例
config = Config()