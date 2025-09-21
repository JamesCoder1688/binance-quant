#!/usr/bin/env python3
"""
启动Web应用的简化脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def start_web_server():
    """启动Web服务器"""
    try:
        print("正在启动Web服务器...")

        # 导入web_app模块
        from web_app import app, socketio

        print("✅ Web应用模块导入成功")
        print("🚀 启动Web服务器...")
        print("📍 访问地址: http://localhost:5000")
        print("📱 手机访问: http://你的电脑IP:5000")
        print("按 Ctrl+C 停止服务")

        # 启动服务器
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)

    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_web_server()