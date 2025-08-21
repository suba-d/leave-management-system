#!/usr/bin/env python3
"""
應用功能測試腳本
"""
import os
import tempfile
from datetime import datetime, date, timedelta

# 設置測試環境
os.environ['FLASK_ENV'] = 'testing'

from app import create_app
from app.config import TestingConfig
from app.models import db, User, LeaveRecord
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.leave_service import LeaveService

def test_app_basic_functionality():
    """測試應用基本功能"""
    print("🧪 開始測試應用基本功能...")
    
    # 創建測試應用
    app = create_app(TestingConfig)
    
    with app.app_context():
        try:
            # 1. 測試資料庫初始化
            print("📊 測試資料庫初始化...")
            db.create_all()
            print("✅ 資料庫初始化成功")
            
            # 2. 測試用戶創建
            print("👤 測試用戶管理服務...")
            test_user = UserService.create_user("testuser", "testpass")
            print(f"✅ 用戶創建成功: {test_user.username}")
            
            # 3. 測試管理員創建
            admin_user = User(
                username="admin",
                password="admin123",
                is_admin=True,
                vacation_days=10,
                sick_days=5,
                personal_days=14
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ 管理員用戶創建成功")
            
            # 4. 測試身份驗證
            print("🔐 測試身份驗證服務...")
            auth_user = AuthService.authenticate_user("testuser", "testpass")
            print(f"✅ 身份驗證成功: {auth_user.username}")
            
            # 5. 測試請假申請
            print("📝 測試請假服務...")
            leave_data = {
                'leave_type': '特休',
                'start_date': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'end_date': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'half_day': False,
                'reason': '測試請假'
            }
            
            leave_record = LeaveService.create_leave_request(test_user, leave_data)
            print(f"✅ 請假申請成功: {leave_record.leave_type} {leave_record.days} 天")
            
            # 6. 測試請假統計
            print("📈 測試請假統計...")
            leave_records = LeaveService.get_user_leave_records(test_user.id)
            stats = LeaveService.calculate_annual_leave_stats(leave_records, datetime.now().year)
            print(f"✅ 統計計算成功: 特休已用 {stats['annual_leave_days']} 天")
            
            # 7. 測試用戶更新
            print("🔄 測試用戶更新...")
            UserService.update_user_leave_days(test_user.id, {
                'annual_leave': 15,
                'sick_leave': 8
            })
            print("✅ 用戶更新成功")
            
            # 8. 測試請假記錄刪除
            print("🗑️  測試請假記錄刪除...")
            LeaveService.delete_leave_record(leave_record.id)
            print("✅ 請假記錄刪除成功")
            
            print("\n🎉 所有基本功能測試通過！")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

def test_route_endpoints():
    """測試路由端點"""
    print("\n🛣️  測試路由端點...")
    
    app = create_app(TestingConfig)
    client = app.test_client()
    
    with app.app_context():
        db.create_all()
        
        try:
            # 測試主頁
            response = client.get('/')
            print(f"✅ 主頁路由: {response.status_code} (重定向到登入)")
            
            # 測試登入頁面
            try:
                response = client.get('/auth/login')
                print(f"✅ 登入頁面: {response.status_code}")
            except Exception as e:
                print(f"❌ 登入頁面錯誤: {e}")
                return False
            
            # 測試其他受保護路由（應該重定向到登入）
            protected_routes = [
                '/leave/dashboard',
                '/leave/apply',
                '/admin/',
            ]
            
            for route in protected_routes:
                response = client.get(route)
                if response.status_code in [302, 401]:  # 重定向或未授權
                    print(f"✅ 受保護路由 {route}: {response.status_code}")
                else:
                    print(f"⚠️  路由 {route} 可能有問題: {response.status_code}")
            
            print("✅ 路由端點測試完成")
            
        except Exception as e:
            print(f"❌ 路由測試失敗: {e}")
            return False
    
    return True

def test_template_paths():
    """測試模板路徑"""
    print("\n📄 檢查模板文件...")
    
    templates = [
        'templates/login.html',
        'templates/base.html',
        'templates/leave.html',
        'templates/admin.html',
        'templates/user_records.html'
    ]
    
    all_found = True
    for template in templates:
        if os.path.exists(template):
            print(f"✅ 模板存在: {template}")
        else:
            print(f"❌ 模板缺失: {template}")
            all_found = False
    
    return all_found

if __name__ == "__main__":
    print("🚀 開始全面功能測試...\n")
    
    # 測試基本功能
    basic_test = test_app_basic_functionality()
    
    # 測試路由
    route_test = test_route_endpoints()
    
    # 測試模板
    template_test = test_template_paths()
    
    print(f"\n📊 測試結果總結:")
    print(f"✅ 基本功能: {'通過' if basic_test else '失敗'}")
    print(f"✅ 路由端點: {'通過' if route_test else '失敗'}")
    print(f"✅ 模板文件: {'通過' if template_test else '失敗'}")
    
    if all([basic_test, route_test, template_test]):
        print("\n🎉 所有測試通過！重構後的應用功能正常！")
    else:
        print("\n⚠️  部分測試失敗，需要檢查相關問題")