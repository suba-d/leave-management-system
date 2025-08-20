from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .leave_record import LeaveRecord

__all__ = ['db', 'User', 'LeaveRecord']