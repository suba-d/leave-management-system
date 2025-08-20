import os
from datetime import timedelta


class Config:
    """應用配置類"""
    
    # Flask 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or '26322655'
    
    # 資料庫配置
    DB_HOST = os.environ.get('DB_HOST') or "leavedb.cv6m4ssak23j.ap-northeast-1.rds.amazonaws.com"
    DB_NAME = os.environ.get('DB_NAME') or "leave_system"
    DB_USERNAME = os.environ.get('DB_USERNAME') or "admin"
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or "Keira0417"
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google API 配置
    GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE') or 'credentials.json'
    GOOGLE_CALENDAR_ID = os.environ.get('GOOGLE_CALENDAR_ID') or 'c_5a0402820b477847c2ada72002977033714ea8385aed41bbc6962789ab53783f@group.calendar.google.com'
    
    # 請假業務配置
    MAX_LEAVE_DAYS = int(os.environ.get('MAX_LEAVE_DAYS', 5))
    MAX_FUTURE_DAYS = int(os.environ.get('MAX_FUTURE_DAYS', 60))
    
    # 預設請假天數配置
    DEFAULT_LEAVE_DAYS = {
        'annual_leave': int(os.environ.get('DEFAULT_ANNUAL_LEAVE', 10)),
        'sick_leave': int(os.environ.get('DEFAULT_SICK_LEAVE', 5)),
        'personal_leave': int(os.environ.get('DEFAULT_PERSONAL_LEAVE', 14)),
        'menstrual_leave': int(os.environ.get('DEFAULT_MENSTRUAL_LEAVE', 5)),
        'family_care_leave': int(os.environ.get('DEFAULT_FAMILY_CARE_LEAVE', 7)),
        'compassionate_leave': int(os.environ.get('DEFAULT_COMPASSIONATE_LEAVE', 3))
    }
    
    # 請假類型映射
    LEAVE_TYPE_MAPPING = {
        '特休': 'vacation_days',
        '病假': 'sick_days',
        '事假': 'personal_days',
        '生理假': 'menstrual_days',
        '家庭照顧假': 'family_care_days',
        '同情假': 'compassionate_days',
    }
    
    # 檔案上傳配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or '/tmp'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 日誌配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'


class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """測試環境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}