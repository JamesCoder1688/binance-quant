#!/usr/bin/env python3
"""
币安量化交易信号生成器 - 启动脚本
简化版启动入口
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入主程序
from src.main import main

if __name__ == "__main__":
    main()