#!/usr/bin/env python3
"""
應用程式健康檢查模組
用於監控系統狀態和服務可用性
"""

import os
import time
import json
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from ..models import db, User
from sqlalchemy import text

# 建立 Blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """基本健康檢查端點"""
    try:
        # 檢查資料庫連線
        db.session.execute(text('SELECT 1'))
        
        # 檢查應用程式基本狀態
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.2-deploy-test',
            'checks': {
                'database': 'ok',
                'application': 'ok'
            }
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        error_status = {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'checks': {
                'database': 'error',
                'application': 'ok'
            }
        }
        
        current_app.logger.error(f"健康檢查失敗: {e}")
        return jsonify(error_status), 503

@health_bp.route('/health/detailed')
def detailed_health_check():
    """詳細健康檢查端點"""
    try:
        start_time = time.time()
        
        # 檢查資料庫連線和查詢效能
        db_start = time.time()
        db.session.execute(text('SELECT 1'))
        db_time = time.time() - db_start
        
        # 檢查用戶表是否正常
        user_count = User.query.count()
        
        # 檢查 Google Calendar API 連線
        google_api_status = 'ok'
        try:
            if os.path.exists('credentials.json'):
                from google.oauth2.service_account import Credentials
                creds = Credentials.from_service_account_file('credentials.json')
                google_api_status = 'ok'
            else:
                google_api_status = 'warning - credentials file missing'
        except Exception:
            google_api_status = 'error'
        
        # 檢查檔案系統權限
        logs_writable = 'ok'
        try:
            if not os.path.exists('logs'):
                os.makedirs('logs')
            test_file = 'logs/health_check_test.tmp'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception:
            logs_writable = 'error'
        
        # 檢查請假記錄表
        leave_records_status = 'ok'
        try:
            from ..models import LeaveRecord
            leave_count = LeaveRecord.query.count()
        except Exception:
            leave_records_status = 'error'
            leave_count = 0
        
        total_time = time.time() - start_time
        
        detailed_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': round(total_time * 1000, 2),
            'checks': {
                'database': {
                    'status': 'ok',
                    'response_time_ms': round(db_time * 1000, 2),
                    'user_count': user_count
                },
                'application': {
                    'status': 'ok',
                    'uptime': 'unknown'
                },
                'google_api': {
                    'status': google_api_status
                },
                'file_system': {
                    'logs_writable': logs_writable
                },
                'leave_records': {
                    'status': leave_records_status,
                    'total_count': leave_count
                }
            }
        }
        
        return jsonify(detailed_status), 200
        
    except Exception as e:
        current_app.logger.error(f"詳細健康檢查失敗: {e}")
        
        error_status = {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'checks': {
                'database': 'error',
                'application': 'unknown'
            }
        }
        
        return jsonify(error_status), 503

@health_bp.route('/metrics')
def basic_metrics():
    """基本監控指標端點"""
    try:
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'application': {
                'name': 'leave-management-system',
                'version': '1.0.0'
            },
            'database': {
                'total_users': User.query.count(),
                'active_sessions': 'unknown'  # TODO: 實作 session 計數
            }
        }
        
        return jsonify(metrics), 200
        
    except Exception as e:
        current_app.logger.error(f"指標收集失敗: {e}")
        return jsonify({'error': str(e)}), 500