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

# models.py 裏頭只定義: db = SQLAlchemy() + (User, LeaveRecord)
# 這裡直接 from models import db, User, LeaveRecord
from models import db, User, LeaveRecord

# forms.py 如果你真的有用 WTForms，就 import；若沒用到可移除
from forms import LoginForm  # 看你實際需求

SCOPES = ['https://www.googleapis.com/auth/drive.file']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)


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
    file_metadata = {'name': file_name}
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]

    media = MediaFileUpload(file_path, mimetype='application/pdf')
    uploaded_file = drive_service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields='id'
    ).execute()
    return f"https://drive.google.com/file/d/{uploaded_file['id']}/view"


def create_app():
    """
    建立並回傳 Flask 應用程式 (採用應用工廠模式)
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'  # 請替換為更安全的 key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:26322655@localhost/leave_system'
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
        user = User.query.get_or_404(user_id)
        leave_records = LeaveRecord.query.filter_by(user_id=user_id).all()
        return render_template('user_records.html', user=user, leave_records=leave_records)

    @app.route('/base', methods=['GET'])
    @login_required
    def base():
        # 取得當前使用者請假紀錄
        leave_records = LeaveRecord.query.filter_by(user_id=current_user.id).all()
        return render_template(
            'base.html',
            username=current_user.username,
            vacation_days=current_user.vacation_days,
            sick_days=current_user.sick_days,
            leave_records=leave_records
        )

    @app.route('/add_user', methods=['POST'])
    @login_required
    def add_user():
        if not current_user.is_admin:
            return redirect(url_for('base'))

        username = request.form['username'].lower()
        password = request.form['password']
        annual_leave = request.form['annual_leave']
        sick_leave = request.form['sick_leave']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f'帳號 {username} 已存在', 'danger')
            return redirect(url_for('admin'))

        new_user = User(
            username=username,
            password=password,
            vacation_days=annual_leave,
            sick_days=sick_leave
        )
        db.session.add(new_user)

        try:
            db.session.commit()
            flash('新增用戶成功！', 'success')
        except IntegrityError:
            db.session.rollback()
            flash(f'帳號 {username} 已存在或其他資料庫錯誤', 'danger')

        return redirect(url_for('admin'))

    @app.route('/leave', methods=['GET', 'POST'])
    @login_required
    def leave():
        if request.method == 'GET':
            return render_template('leave.html')

        if request.method == 'POST':
            file = request.files.get('receipt')
            leave_type = request.form.get('leave_type')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            is_half_day = (request.form.get('half_day') == 'on')
            reason = request.form.get('reason')

            # 計算天數
            try:
                leave_days = calculate_half_day_leave_days(start_date, end_date, is_half_day)
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('leave'))

            # 如果是病假 + 有附加檔案，就上傳到 Google Drive
            receipt_url = None
            if file and leave_type == '病假':
                file_path = f"/tmp/{file.filename}"
                file.save(file_path)
                receipt_url = upload_to_google_drive(file_path, file.filename)
                os.remove(file_path)

            # 檢查剩餘天數
            if leave_type == '特休':
                if current_user.vacation_days < leave_days:
                    flash("特休天數不足", 'danger')
                    return redirect(url_for('leave'))
                current_user.vacation_days -= leave_days
            elif leave_type == '病假':
                if current_user.sick_days < leave_days:
                    flash("病假天數不足", 'danger')
                    return redirect(url_for('leave'))
                current_user.sick_days -= leave_days

            # 建立請假紀錄
            new_leave = LeaveRecord(
                user_id=current_user.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                half_day=is_half_day,
                receipt_url=receipt_url
            )
            db.session.add(new_leave)
            db.session.commit()

            flash("請假成功", 'success')
            return redirect(url_for('base'))

    @app.route('/update_user/<int:user_id>', methods=['POST'])
    @login_required
    def update_user(user_id):
        if not current_user.is_admin:
            return redirect(url_for('base'))

        annual_leave = request.form['annual_leave']
        sick_leave = request.form['sick_leave']

        user = User.query.get(user_id)
        if user:
            user.vacation_days = annual_leave
            user.sick_days = sick_leave
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
        db.session.delete(leave_record)
        db.session.commit()
    
        redirect_to = request.args.get('redirect_to')
        if redirect_to == 'user_records':
           return redirect(url_for('user_records', user_id=leave_record.user_id))
        else:
           return redirect(url_for('admin'))

    # 工廠函式最後一定要 return app
    return app