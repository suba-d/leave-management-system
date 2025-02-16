# app.py
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_migrate import Migrate
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import os
import boto3
import json
from werkzeug.utils import secure_filename
import logging
from botocore.exceptions import ClientError

# models.py 裏頭只定義: db = SQLAlchemy() + (User, LeaveRecord)
# 這裡直接 from models import db, User, LeaveRecord
from models import db, User, LeaveRecord

# forms.py 如果你真的有用 WTForms，就 import；若沒用到可移除
from forms import LoginForm  # 看你實際需求

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/calendar'
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')

try:
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    calendar_service = build('calendar', 'v3', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    logging.info("Google Calendar API 初始化成功")
except Exception as e:
    logging.error(f"Google Calendar API 初始化失敗: {e}")
    exit(1)


def create_calendar_event(summary, start_date, end_date, calendar_id='c_5a0402820b477847c2ada72002977033714ea8385aed41bbc6962789ab53783f@group.calendar.google.com'):
    try:
        event = {
            'summary': summary,
            'start': {'dateTime': start_date.isoformat() + 'Z'},
            'end': {'dateTime': end_date.isoformat() + 'Z'},
        }
        logging.debug(f"Creating event: {event}")
        event = calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
        logging.info(f"Event created successfully: {event.get('htmlLink')}")
        return event.get('htmlLink')
    except Exception as e:
        logging.error(f"Error creating calendar event: {e}")
        return None


def calculate_half_day_leave_days(start_date_str, end_date_str, is_half_day):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    if end_date < start_date:
        raise ValueError("結束日期必須大於或等於開始日期")
    total_days = (end_date - start_date).days + 1

    # 單日範圍且勾選半天
    if total_days == 1:
        return 0.5 if is_half_day else 1.0

    # 多日範圍，若勾選半天，就扣 0.5
    leave_days = total_days
    if is_half_day:
        leave_days -= 0.5
    return leave_days


def upload_to_google_drive(file_path, file_name, parent_folder_id=None):
    try:
        import mimetypes
        mimetype, _ = mimetypes.guess_type(file_path)

        # 設定文件的基本元數據
        file_metadata = {'name': file_name}
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]

        # 上傳文件到 Google Drive
        media = MediaFileUpload(file_path, mimetype=mimetype or 'application/octet-stream')
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        # 設置文件為公開可見
        drive_service.permissions().create(
            fileId=uploaded_file['id'],
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()

        # 返回標準的分享 URL
        return f"https://drive.google.com/uc?export=view&id={uploaded_file['id']}"

    except Exception as e:
        logging.error(f"Error uploading file to Google Drive: {e}")
        return None


def get_rds_credentials():
    secret_name = "rds!db-6505dd7b-6e58-4b77-b54a-bae7b407167b"
    region_name = "ap-northeast-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        return json.loads(get_secret_value_response['SecretString'])
    except ClientError as e:
        logging.error(f"❌ 無法從 Secrets Manager 獲取密碼: {e}")
        raise e


def create_app():
    """
    建立並回傳 Flask 應用程式 (採用應用工廠模式)
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '26322655'  # 使用您自己的密鑰，這裡我用您之前用過的數字作為示例

    # 取得 RDS 密碼
    rds_secret = get_rds_credentials()
    if not rds_secret:
        raise Exception("❌ 無法取得 RDS 資訊，請檢查 Secrets Manager 設定")

    # 設定 SQLAlchemy 連線字串
    DB_HOST = "leavedb.cv6m4ssak23j.ap-northeast-1.rds.amazonaws.com"
    DB_NAME = "leave_system"
    DB_USERNAME = rds_secret["username"]
    DB_PASSWORD = rds_secret["password"]

    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 1. 初始化 db
    db.init_app(app)

    # 2. 初始化 Migrate
    migrate = Migrate(app, db)

    # 3. 初始化 LoginManager
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ----------------------
    # 在 create_app() 裡宣告所有 route
    # ----------------------

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            # 如果是管理員，就進 /admin；否則 /base
            return redirect(url_for('admin' if current_user.is_admin else 'base'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').lower()
            password = request.form.get('password', '').lower()

            user = User.query.filter_by(username=username).first()
            if user and user.password.lower() == password:
                login_user(user)
                return redirect(url_for('admin' if user.is_admin else 'base'))
            else:
                flash('帳號或密碼錯誤', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/admin', methods=['GET'])
    @login_required
    def admin():
        if not current_user.is_admin:
            return redirect(url_for('base'))
    
        users = User.query.filter_by(is_admin=False).all()
        leave_records = {}
    
        for user in users:
            leave_records[user.id] = LeaveRecord.query.filter_by(user_id=user.id)\
                .order_by(LeaveRecord.start_date.desc())\
                .limit(5)\
                .all()
    
        return render_template('admin.html', users=users, leave_records=leave_records)

    @app.route('/user_records/<int:user_id>')
    @login_required
    def user_records(user_id):
        user = User.query.get(user_id)
        leave_records = LeaveRecord.query.filter_by(user_id=user_id).all()

        # 計算每年度的請假紀錄統計
        current_year = datetime.now().year
        annual_leave_days = 0
        sick_leave_days = 0
        personal_leave_days=0
        menstrual_leave_days=0
        family_care_leave_days=0
        compassionate_leave_days=0

        for record in leave_records:
            if record.start_date.year == current_year:
                if record.leave_type == '特休':
                    annual_leave_days += record.days
                elif record.leave_type == '病假':
                    sick_leave_days += record.days
                elif record.leave_type == '事假':
                    personal_leave_days += record.days
                elif record.leave_type == '生理假':
                    menstrual_leave_days += record.days
                elif record.leave_type == '家庭照顧假':
                    family_care_leave_days += record.days
                elif record.leave_type == '同情假':
                    compassionate_leave_days += record.days            

        return render_template('user_records.html', user=user, leave_records=leave_records, 
                       annual_leave_days=annual_leave_days, sick_leave_days=sick_leave_days,personal_leave_days=personal_leave_days,menstrual_leave_days=menstrual_leave_days,family_care_leave_days=family_care_leave_days,compassionate_leave_days=compassionate_leave_days ,current_year=current_year)

    @app.route('/base', methods=['GET'])
    @login_required
    def base():
        # 取得當前使用者請假紀錄
        
        leave_records = LeaveRecord.query.filter_by(user_id=current_user.id).all()
        # 計算每年度的請假紀錄統計
        current_year = datetime.now().year
        annual_leave_days = 0
        sick_leave_days = 0
        personal_leave_days=0
        menstrual_leave_days=0
        family_care_leave_days=0
        compassionate_leave_days=0
        for record in leave_records:
            if record.start_date.year == current_year:
                if record.leave_type == '特休':
                    annual_leave_days += record.days
                elif record.leave_type == '病假':
                    sick_leave_days += record.days
                elif record.leave_type == '事假':
                    personal_leave_days += record.days
                elif record.leave_type == '生理假':
                    menstrual_leave_days += record.days
                elif record.leave_type == '家庭照顧假':
                    family_care_leave_days += record.days
                elif record.leave_type == '同情假':
                    compassionate_leave_days += record.days        
        return render_template(
            'base.html',
            username=current_user.username,
            vacation_days=current_user.vacation_days,
            sick_days=current_user.sick_days,
            personal_days=current_user.personal_days,
            menstrual_days=current_user.menstrual_days,
            family_care_days=current_user.family_care_days,
            compassionate_days=current_user.compassionate_days,
            leave_records=leave_records,
            annual_leave_days=annual_leave_days,
            current_year=current_year,
            sick_leave_days=sick_leave_days,
            personal_leave_days=personal_leave_days,
            menstrual_leave_days=menstrual_leave_days,
            family_care_leave_days=family_care_leave_days,
            compassionate_leave_days=compassionate_leave_days
        )

    @app.route('/add_user', methods=['POST'])
    @login_required
    def add_user():
        if not current_user.is_admin:
            return redirect(url_for('base'))

        username = request.form['username'].lower()
        username = username.capitalize()  # 第一個字母大寫，其餘字母小寫
        password = request.form['password']
        annual_leave = 10
        sick_leave = 5
        personal_leave = 14
        menstrual_leave = 5
        family_care_leave = 7
        compassionate_leave = 3

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f'帳號 {username} 已存在', 'danger')
            return redirect(url_for('admin'))

        new_user = User(
            username=username,
            password=password,
            vacation_days=annual_leave,
            sick_days=sick_leave,
            personal_days=personal_leave,
            menstrual_days=menstrual_leave,
            family_care_days=family_care_leave,
            compassionate_days=compassionate_leave
            
        )
        db.session.add(new_user)

        try:
            db.session.commit()
            flash('新增用戶成功！', 'success')
        except IntegrityError:
            db.session.rollback()
            flash(f'帳號 {username} 已存在或其他資料庫錯誤', 'danger')

        return redirect(url_for('admin'))
    @app.route('/update_password/<int:user_id>', methods=['POST'])
    @login_required
    def update_password(user_id):
        user = User.query.get_or_404(user_id)
        new_password = request.form['new_password']
        user.password = new_password  # 假設你有適當的密碼哈希處理
        db.session.commit()
        flash('密碼更新成功', 'success')
        return redirect(url_for('user_records', user_id=user_id))

    @app.route('/leave', methods=['GET', 'POST'])
    @login_required
    def leave():
        receipt_url = None
        if request.method == 'POST':
            leave_type = request.form['leave_type']
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
            half_day = 'half_day' in request.form
            reason = request.form.get('reason', '')
            receipt = request.files.get('receipt')
            receipt_url = None

            # 上傳收據處理
            if receipt:
                 filename = secure_filename(receipt.filename)
                 file_path = os.path.join('/tmp', filename)
                 receipt.save(file_path)
                 receipt_url = upload_to_google_drive(file_path, filename)
                 os.remove(file_path)  # 刪除臨時文件

                 if not receipt_url:
                     flash('上傳收據失敗', 'warning')
                     return redirect(url_for('leave'))
            # 檢查開始日期不能比結束日期晚
            if start_date > end_date:
                flash('開始日期不能比結束日期晚', 'danger')
                return redirect(url_for('leave'))

            # 計算請假天數
            delta = end_date - start_date
            days = delta.days + 1  # 包含開始日期和結束日期
            if half_day:
                days -= 0.5

            # 檢查剩餘天數是否足夠
            leave_days_mapping = {
                '特休': 'vacation_days',
                '病假': 'sick_days',
                '事假': 'personal_days',
                '生理假': 'menstrual_days',
                '家庭照顧假': 'family_care_days',
                '同情假': 'compassionate_days',
            }
            if leave_type in leave_days_mapping:
                remaining_days = getattr(current_user, leave_days_mapping[leave_type])
                if days > remaining_days:
                    flash(f'{leave_type} 剩餘天數不足', 'danger')
                    return redirect(url_for('leave'))

            # 更新使用者的特休或病假天數
                setattr(current_user, leave_days_mapping[leave_type], remaining_days - days)
            else:
                flash('未知的請假類型', 'danger')
                return redirect(url_for('leave'))

            # 新增請假記錄
            leave_record = LeaveRecord(
                user_id=current_user.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                half_day=half_day,
                reason=reason,
                receipt_url=receipt_url,
                days=days
            )

            try:
                db.session.add(leave_record)
                db.session.commit()
                flash('請假申請成功', 'success')

                # 創建 Google 日曆事件
                event_summary = f"{current_user.username} - {leave_type}"
                calendar_event = create_calendar_event(event_summary, start_date, end_date)

                if calendar_event:
                    flash('請假已同步至 Google 日曆', 'success')
                else:
                    flash('請假同步 Google 日曆失敗', 'warning')

            except Exception as e:
                db.session.rollback()
                logging.error(f"Error saving leave record to database: {e}")
                flash('請假申請失敗，請稍後再試', 'danger')

            return redirect(url_for('leave'))

        return render_template('leave.html', username=current_user.username, receipt_url=receipt_url)

    @app.route('/update_user/<int:user_id>', methods=['POST'])
    @login_required
    def update_user(user_id):
        if not current_user.is_admin:
            return redirect(url_for('base'))

        annual_leave = request.form['annual_leave']
        sick_leave = request.form['sick_leave']
        personal_leave=request.form['personal_leave']
        menstrual_leave=request.form['menstrual_leave']
        family_care_leave=request.form['family_care_leave']
        compassionate_leave=request.form['compassionate_leave']
        

        user = User.query.get(user_id)
        if user:
            user.vacation_days = annual_leave
            user.sick_days = sick_leave
            user.personal_days=personal_leave
            user.menstrual_days=menstrual_leave
            user.family_care_days=family_care_leave
            user.compassionate_days=compassionate_leave
            db.session.commit()
            flash('用戶天數更新成功', 'success')
        else:
            flash('找不到該用戶', 'danger')

        return redirect(url_for('admin'))

    @app.route('/delete_user/<int:user_id>', methods=['POST'])
    @login_required
    def delete_user(user_id):
        if not current_user.is_admin:
            return redirect(url_for('base'))

        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash('用戶刪除成功', 'success')
        else:
            flash('找不到該用戶', 'danger')
        return redirect(url_for('admin'))

    @app.route('/delete_leave/<int:leave_id>', methods=['POST'])
    @login_required
    def delete_leave(leave_id):
        leave_record = LeaveRecord.query.get_or_404(leave_id)
        user_id = leave_record.user_id
        db.session.delete(leave_record)
        db.session.commit()
        flash('刪除請假紀錄成功', 'success')
        
        # 根據 referer 來決定跳轉頁面
        referer = request.headers.get("Referer")
        if referer and 'admin' in referer:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('user_records', user_id=user_id))

    @app.route('/update_leave_days/<int:leave_id>', methods=['POST'])
    @login_required
    def update_leave_days(leave_id):
        leave_record = LeaveRecord.query.get_or_404(leave_id)
        try:
            leave_days = float(request.form['leave_days'])
            if leave_days <= 0:
                flash('請假天數必須大於0', 'danger')
            else:
                leave_record.leave_days = leave_days
                db.session.commit()
                flash('更新請假天數成功', 'success')
        except ValueError:
            flash('請輸入有效的請假天數', 'danger')
        
        return redirect(url_for('admin'))

    # 工廠函式最後一定要 return app 
    return app
