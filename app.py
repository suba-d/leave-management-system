from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from forms import LoginForm
from datetime import datetime,timedelta
from models import db, User, LeaveRecord
from sqlalchemy.exc import IntegrityError,SQLAlchemyError 
from flask_migrate import Migrate
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import os


# 授權和初始化 Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def calculate_half_day_leave_days(start_date, end_date, is_half_day):
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 確保結束日期大於等於開始日期
    if end_date < start_date:
        raise ValueError("結束日期必須大於或等於開始日期")

    total_days = (end_date - start_date).days + 1

    # 如果請假範圍只有一天且勾選了半天
    if total_days == 1:
        return 0.5 if is_half_day else 1

    # 處理多日範圍
    leave_days = total_days

    # 勾選了半天，計算開始日或結束日的半天影響
    if is_half_day:
        leave_days -= 0.5  # 假設勾選半天，扣除半天

    return leave_days

def upload_to_google_drive(file_path, file_name, parent_folder_id=None):
    file_metadata = {'name': file_name}
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]

    media = MediaFileUpload(file_path, mimetype='application/pdf')
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return f"https://drive.google.com/file/d/{uploaded_file['id']}/view"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 替換為更安全的密鑰
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:26322655@localhost/leave_system'  # 替換為你的 MySQL 資料庫連接
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models here
import models
# 初始化資料庫
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin' if current_user.is_admin else 'base'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').lower()  # 將用戶輸入的帳號轉為小寫
        password = request.form.get('password').lower()  # 將用戶輸入的密碼轉為小寫

        # 在查詢和比對時將資料庫中的帳號和密碼也轉為小寫
        user = User.query.filter_by(username=username).first()
        if user and user.password.lower() == password:  # 比對時轉小寫
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('base'))
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

    # 獲取非管理員的用戶列表
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin.html', users=users)

@app.route('/user_records/<int:user_id>')
def user_records(user_id):
    user = User.query.get_or_404(user_id)
    leave_records = LeaveRecord.query.filter_by(user_id=user_id).all()
    return render_template('user_records.html', user=user, leave_records=leave_records)


@app.route('/base', methods=['GET'])
@login_required
def base():
    # 獲取當前用戶的請假紀錄
    leave_records = LeaveRecord.query.filter_by(user_id=current_user.id).all()

    # 傳遞請假紀錄到模板
    return render_template(
        'base.html',
        username=current_user.username,
        vacation_days=current_user.vacation_days,
        sick_days=current_user.sick_days,
        leave_records=leave_records  # 確保帶上收據資料
    )

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username'].lower()  # 存入資料庫前轉為小寫
    password = request.form['password']  # 密碼可以視需求是否區分大小寫
    annual_leave = request.form['annual_leave']
    sick_leave = request.form['sick_leave']

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash(f'帳號 {username} 已存在，請使用其他名稱', 'danger')
        return redirect(url_for('admin'))

    new_user = User(
        username=username,  # 存小寫帳號
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
        # 返回表單頁面
        return render_template('leave.html')
    
    if request.method == 'POST':
        file = request.files.get('receipt')
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        is_half_day = request.form.get('half_day') == 'on'
        reason = request.form.get('reason')
        try:
            # 使用 calculate_half_day_leave_days 函数计算天数
            leave_days = calculate_half_day_leave_days(start_date, end_date, is_half_day)
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('leave'))


        # 處理收據
        receipt_url = None
        if file and leave_type == '病假':
            file_path = f"/tmp/{file.filename}"
            file.save(file_path)
            receipt_url = upload_to_google_drive(file_path, file.filename)
            os.remove(file_path)

        # 檢查剩餘天數是否足夠
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

        # 創建請假記錄
        new_leave = LeaveRecord(
            user_id=current_user.id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            half_day=is_half_day,
            receipt_url=receipt_url  # 儲存收據URL
        )
        db.session.add(new_leave)
        db.session.commit()

        flash("請假成功", 'success')
        return redirect(url_for('base'))

@app.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    annual_leave = request.form['annual_leave']
    sick_leave = request.form['sick_leave']
    
    # 找到此 user_id 的使用者，然後更新
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
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('用戶刪除成功', 'success')
    else:
        flash('找不到該用戶', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/delete_leave/<int:leave_id>', methods=['POST'])
def delete_leave(leave_id):
    # 查找請假記錄
    leave_record = LeaveRecord.query.get(leave_id)
    if not leave_record:
        flash('請假記錄不存在', 'error')
        return redirect(url_for('user_records', user_id=leave_record.user_id))
    
    # 刪除記錄
    db.session.delete(leave_record)
    db.session.commit()
    flash('成功刪除請假記錄', 'success')
    return redirect(url_for('user_records', user_id=leave_record.user_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 確保資料庫結構已建立
    app.run(debug=True)