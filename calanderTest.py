from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import datetime
import logging

# 設置日曆的 ID
CALENDAR_ID = 'c_5a0402820b477847c2ada72002977033714ea8385aed41bbc6962789ab53783f@group.calendar.google.com'

# 設置服務帳戶憑證文件路徑
SERVICE_ACCOUNT_FILE = '/Users/suba/Documents/請假系統/credentials.json'

# 設置範圍（需要日曆的權限）
SCOPES = ['https://www.googleapis.com/auth/calendar']

# 初始化憑證和服務
try:
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    calendar_service = build('calendar', 'v3', credentials=creds)
    logging.info("Google Calendar API initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Google Calendar API: {e}")
    exit(1)

# 測試創建事件的函數
def test_create_calendar_event():
    try:
        now = datetime.datetime.utcnow()
        event = {
            'summary': '測試事件',
            'start': {'dateTime': (now + datetime.timedelta(hours=1)).isoformat() + 'Z'},
            'end': {'dateTime': (now + datetime.timedelta(hours=2)).isoformat() + 'Z'},
        }

        created_event = calendar_service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        logging.info(f"Event created: {created_event.get('htmlLink')}")
        print(f"成功創建事件！查看事件：{created_event.get('htmlLink')}")
    except Exception as e:
        logging.error(f"Failed to create event: {e}")
        print(f"創建事件失敗: {e}")

# 執行測試
if __name__ == '__main__':
    test_create_calendar_event()