"""Google 服務整合"""
import os
import mimetypes
from datetime import datetime
from flask import current_app
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from werkzeug.utils import secure_filename
from ..exceptions import ExternalServiceError, FileUploadError


class GoogleService:
    """Google 服務類"""
    
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/calendar'
        ]
        self.credentials = None
        self.calendar_service = None
        self.drive_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """初始化 Google 服務"""
        try:
            credentials_file = current_app.config['GOOGLE_CREDENTIALS_FILE']
            base_dir = os.path.dirname(os.path.abspath(__file__))
            service_account_file = os.path.join(base_dir, '../../', credentials_file)
            
            self.credentials = Credentials.from_service_account_file(
                service_account_file, 
                scopes=self.scopes
            )
            self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            
            current_app.logger.info("Google services initialized successfully")
            
        except Exception as e:
            current_app.logger.error(f"Failed to initialize Google services: {e}")
            raise ExternalServiceError(f"Google API 初始化失敗: {e}")
    
    def create_calendar_event(self, summary, start_date, end_date, calendar_id=None):
        """創建 Google Calendar 事件"""
        if not calendar_id:
            calendar_id = current_app.config['GOOGLE_CALENDAR_ID']
        
        try:
            # 處理日期格式 - 使用全天事件格式
            if isinstance(start_date, str):
                start_date_str = start_date
            else:
                start_date_str = start_date.strftime('%Y-%m-%d')
            
            if isinstance(end_date, str):
                end_date_str = end_date
            else:
                end_date_str = end_date.strftime('%Y-%m-%d')
            
            # 如果是請假，通常是全天事件，使用 date 而不是 dateTime
            # 結束日期需要加一天（Google Calendar 全天事件的結束日期是不包含的）
            from datetime import datetime, timedelta
            end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date_obj += timedelta(days=1)
            end_date_str = end_date_obj.strftime('%Y-%m-%d')
            
            event = {
                'summary': summary,
                'start': {'date': start_date_str},
                'end': {'date': end_date_str},
                'description': f'請假申請 - {summary}'
            }
            
            current_app.logger.debug(f"Creating calendar event: {event}")
            
            created_event = self.calendar_service.events().insert(
                calendarId=calendar_id, 
                body=event
            ).execute()
            
            current_app.logger.info(f"Calendar event created: {created_event.get('htmlLink')}")
            return created_event.get('htmlLink')
            
        except Exception as e:
            current_app.logger.error(f"Error creating calendar event: {e}")
            # 不拋出異常，讓主要業務流程繼續
            return None
    
    def upload_to_drive(self, file_path, file_name, parent_folder_id=None):
        """上傳檔案到 Google Drive"""
        try:
            # 猜測檔案類型
            mimetype, _ = mimetypes.guess_type(file_path)
            
            # 設定檔案元數據
            file_metadata = {'name': file_name}
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            # 上傳檔案
            media = MediaFileUpload(
                file_path, 
                mimetype=mimetype or 'application/octet-stream'
            )
            uploaded_file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            # 設置檔案為公開可見
            self.drive_service.permissions().create(
                fileId=uploaded_file['id'],
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            # 返回公開分享連結
            share_url = f"https://drive.google.com/uc?export=view&id={uploaded_file['id']}"
            current_app.logger.info(f"File uploaded to Google Drive: {share_url}")
            return share_url
            
        except Exception as e:
            current_app.logger.error(f"Error uploading to Google Drive: {e}")
            raise ExternalServiceError(f"Google Drive 上傳失敗: {e}")
    
    def process_receipt_upload(self, receipt_file):
        """處理收據上傳"""
        if not receipt_file or not receipt_file.filename:
            return None
        
        try:
            filename = secure_filename(receipt_file.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp')
            
            # 確保上傳資料夾存在
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file_path = os.path.join(upload_folder, filename)
            receipt_file.save(file_path)
            
            # 上傳到 Google Drive
            receipt_url = self.upload_to_drive(file_path, filename)
            
            # 清理臨時檔案
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return receipt_url
            
        except Exception as e:
            current_app.logger.error(f"Receipt upload error: {e}")
            raise FileUploadError('檔案上傳過程發生錯誤')


# 全域 Google 服務實例
google_service = None

def get_google_service():
    """獲取 Google 服務實例"""
    global google_service
    if google_service is None:
        google_service = GoogleService()
    return google_service