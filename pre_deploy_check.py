#!/usr/bin/env python3
"""
部署前檢查腳本
確保重構後的應用可以正常部署
"""
import os
import sys
import subprocess

def check_import():
    """檢查應用是否可以正常導入"""
    print("🔍 檢查應用導入...")
    try:
        from app import create_app
        app = create_app()
        print("✅ 應用導入成功")
        return True
    except Exception as e:
        print(f"❌ 應用導入失敗: {e}")
        return False

def check_run_py():
    """檢查 run.py 是否正確"""
    print("🔍 檢查 run.py...")
    try:
        # 模擬 Gunicorn 導入
        import importlib.util
        spec = importlib.util.spec_from_file_location("run", "run.py")
        run_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_module)
        
        if hasattr(run_module, 'app'):
            print("✅ run.py 提供正確的 app 物件")
            return True
        else:
            print("❌ run.py 缺少 app 物件")
            return False
    except Exception as e:
        print(f"❌ run.py 檢查失敗: {e}")
        return False

def check_requirements():
    """檢查依賴是否完整"""
    print("🔍 檢查 requirements.txt...")
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['Flask', 'gunicorn']
        missing = []
        
        for pkg in required_packages:
            if pkg.lower() not in requirements.lower():
                missing.append(pkg)
        
        if missing:
            print(f"❌ requirements.txt 缺少: {', '.join(missing)}")
            return False
        else:
            print("✅ requirements.txt 包含必要依賴")
            return True
    except FileNotFoundError:
        print("❌ 找不到 requirements.txt")
        return False

def check_docker_compatibility():
    """檢查 Docker 兼容性"""
    print("🔍 檢查 Docker 配置...")
    try:
        with open('Dockerfile', 'r') as f:
            dockerfile = f.read()
        
        checks = [
            ('run:app', '應用入口點'),
            ('FLASK_APP=run.py', 'Flask 應用設置'),
            ('requirements.txt', '依賴安裝')
        ]
        
        all_good = True
        for check, desc in checks:
            if check in dockerfile:
                print(f"✅ {desc} 配置正確")
            else:
                print(f"❌ {desc} 配置缺失")
                all_good = False
        
        return all_good
    except FileNotFoundError:
        print("❌ 找不到 Dockerfile")
        return False

def check_env_vars():
    """檢查環境變數配置"""
    print("🔍 檢查環境變數配置...")
    
    # 檢查配置類是否正確
    try:
        from app.config import config
        env_configs = ['development', 'production', 'testing']
        
        for env in env_configs:
            if env in config:
                print(f"✅ {env} 配置存在")
            else:
                print(f"❌ {env} 配置缺失")
                return False
        
        print("✅ 環境配置檢查通過")
        return True
    except Exception as e:
        print(f"❌ 環境配置檢查失敗: {e}")
        return False

def main():
    """主檢查函數"""
    print("🚀 開始部署前檢查...\n")
    
    checks = [
        ("應用導入", check_import),
        ("run.py 檢查", check_run_py),
        ("依賴檢查", check_requirements),
        ("Docker 兼容性", check_docker_compatibility),
        ("環境配置", check_env_vars)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{'='*50}")
        result = check_func()
        results.append((name, result))
        print()
    
    print("="*50)
    print("📊 檢查結果總結:")
    print("="*50)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{name:20} : {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有檢查通過！可以安全部署！")
        print("\n建議部署命令:")
        print("./deploy.sh \"重構應用架構 - 模組化設計\"")
    else:
        print("⚠️  部分檢查失敗，請修復後再部署！")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)