# 請假系統重構說明

## 重構概述

原本的請假系統是一個單體應用，所有代碼都集中在 `app.py` 中。重構後採用模組化架構，將不同功能分離到不同的模組中，提高代碼的可維護性和可擴展性。

## 新架構結構

```
app/
├── __init__.py                 # 應用工廠
├── config.py                   # 配置管理
├── exceptions.py               # 自定義異常
├── models/                     # 數據模型
│   ├── __init__.py
│   ├── user.py                 # 用戶模型
│   └── leave_record.py         # 請假記錄模型
├── services/                   # 業務邏輯服務
│   ├── __init__.py
│   ├── auth_service.py         # 身份驗證服務
│   ├── user_service.py         # 用戶管理服務
│   ├── leave_service.py        # 請假管理服務
│   └── google_service.py       # Google API 服務
├── routes/                     # 路由控制器
│   ├── __init__.py
│   ├── main.py                 # 主要路由
│   ├── auth.py                 # 身份驗證路由
│   ├── admin.py                # 管理員路由
│   └── leave.py                # 請假相關路由
└── utils/                      # 工具函數
    ├── __init__.py
    ├── logging_config.py       # 日誌配置
    ├── error_handlers.py       # 錯誤處理器
    └── validators.py           # 資料驗證工具
```

## 主要改進

### 1. 架構分層
- **配置層**: 統一管理所有配置，支援多環境配置
- **數據層**: 優化數據模型，添加索引和關聯關係
- **服務層**: 分離業務邏輯，提高代碼重用性
- **控制層**: 路由按功能分組，使用藍圖管理
- **工具層**: 提供通用工具和驗證函數

### 2. 錯誤處理
- **自定義異常**: 定義不同類型的業務異常
- **統一錯誤處理**: 全域錯誤處理器，統一錯誤響應格式
- **詳細日誌**: 改進日誌記錄，便於調試和監控

### 3. 資料庫改進
- **索引優化**: 添加必要的數據庫索引提高查詢效能
- **關聯關係**: 正確定義模型間的關聯關係
- **級聯操作**: 適當的級聯刪除保證數據一致性

### 4. 服務分離
- **身份驗證服務**: 處理用戶登入登出邏輯
- **用戶管理服務**: 處理用戶 CRUD 操作
- **請假服務**: 處理請假相關業務邏輯
- **Google 服務**: 整合 Google Calendar 和 Drive API

### 5. 配置管理
- **環境配置**: 支援開發、測試、生產環境配置
- **環境變數**: 敏感信息通過環境變數配置
- **預設值**: 提供合理的預設配置值

## 使用方式

### 啟動應用
```bash
# 啟動開發環境
python run.py

# 指定環境
FLASK_ENV=production python run.py
```

### 環境變數配置
```bash
# 資料庫配置
export DB_HOST="your-db-host"
export DB_USERNAME="your-username"
export DB_PASSWORD="your-password"

# Google API 配置
export GOOGLE_CREDENTIALS_FILE="path/to/credentials.json"
export GOOGLE_CALENDAR_ID="your-calendar-id"

# 應用配置
export SECRET_KEY="your-secret-key"
export MAX_LEAVE_DAYS="5"
```

## 相容性

重構後的應用與原始應用完全相容：
- 數據庫結構不變
- API 端點不變
- 前端模板不變
- 功能行為不變

## 測試

應用已通過基本測試：
- ✅ 應用工廠創建成功
- ✅ 配置載入正常
- ✅ 數據庫連接正常
- ✅ 藍圖註冊成功
- ✅ 錯誤處理器註冊成功

## 備份文件

原始文件已備份：
- `app_original.py` - 原始主應用文件
- `models_original.py` - 原始模型文件

## 後續建議

1. **添加單元測試**: 為各個服務和模型添加測試
2. **API 文檔**: 使用 Flask-RESTx 或 Swagger 生成 API 文檔
3. **快取機制**: 添加 Redis 快取提高效能
4. **監控**: 添加應用監控和指標收集
5. **部署**: 使用 Docker 容器化部署