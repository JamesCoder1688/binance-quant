#!/usr/bin/env python3
"""
诊断脚本 - 检查环境和依赖
"""

import sys
import os
import subprocess

def check_python():
    """检查Python版本"""
    print(f"🐍 Python版本: {sys.version}")
    print(f"📍 Python路径: {sys.executable}")
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = ['flask', 'flask_socketio', 'requests', 'pandas', 'numpy']
    missing_packages = []

    print("\n📦 检查依赖包:")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - 已安装")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)

    return missing_packages

def check_files():
    """检查必要文件"""
    print("\n📁 检查必要文件:")
    required_files = [
        'web_app.py',
        'src/data/binance_api.py',
        'src/indicators/kdj.py',
        'src/indicators/boll.py',
        'web/templates/monitor.html',
        'web/static/js/app.js'
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 文件不存在")
            missing_files.append(file_path)

    return missing_files

def check_port():
    """检查端口占用"""
    print("\n🔌 检查端口5000:")
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
        if ':5000' in result.stdout:
            print("❌ 端口5000被占用")
            lines = [line for line in result.stdout.split('\n') if ':5000' in line]
            for line in lines:
                print(f"   {line.strip()}")
        else:
            print("✅ 端口5000可用")
    except Exception as e:
        print(f"❌ 无法检查端口: {str(e)}")

def test_import():
    """测试导入web_app模块"""
    print("\n🧪 测试模块导入:")
    try:
        # 添加src路径
        src_path = os.path.join(os.getcwd(), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        print("   导入Flask...")
        from flask import Flask
        print("   ✅ Flask导入成功")

        print("   导入SocketIO...")
        from flask_socketio import SocketIO
        print("   ✅ SocketIO导入成功")

        print("   导入web_app...")
        import web_app
        print("   ✅ web_app导入成功")

        return True
    except Exception as e:
        print(f"   ❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 开始环境诊断...")
    print("=" * 50)

    # 检查Python
    check_python()

    # 检查依赖
    missing_packages = check_dependencies()

    # 检查文件
    missing_files = check_files()

    # 检查端口
    check_port()

    # 测试导入
    import_success = test_import()

    print("\n" + "=" * 50)
    print("📋 诊断结果:")

    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("   请运行: pip install " + " ".join(missing_packages))

    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")

    if not import_success:
        print("❌ 模块导入失败")

    if not missing_packages and not missing_files and import_success:
        print("✅ 环境检查通过，可以尝试启动服务")
        print("   运行: python web_app.py")
    else:
        print("❌ 环境存在问题，请先解决上述问题")

if __name__ == "__main__":
    main()