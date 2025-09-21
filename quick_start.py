#!/usr/bin/env python3
"""
快速启动脚本 - 包含错误处理
"""

import sys
import os

def main():
    try:
        print("🚀 开始启动Web应用...")

        # 检查当前目录
        current_dir = os.getcwd()
        print(f"📁 当前目录: {current_dir}")

        # 添加src路径
        src_path = os.path.join(current_dir, 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            print(f"✅ 已添加路径: {src_path}")

        # 检查必要文件
        web_app_path = os.path.join(current_dir, 'web_app.py')
        if not os.path.exists(web_app_path):
            print(f"❌ 找不到web_app.py文件: {web_app_path}")
            return

        print("📦 导入必要模块...")

        # 导入Flask应用
        from web_app import app, socketio
        print("✅ Web应用模块导入成功")

        print("🌐 启动Web服务器...")
        print("📍 本地访问: http://localhost:5000")
        print("📱 手机访问: http://你的电脑IP:5000")
        print("⏹️  按 Ctrl+C 停止服务\n")

        # 启动服务器
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)

    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保所有依赖已安装:")
        print("pip install flask flask-socketio requests pandas numpy")
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n👋 Web服务已停止")

if __name__ == "__main__":
    main()