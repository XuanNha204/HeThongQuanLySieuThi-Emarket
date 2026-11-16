import sqlite3

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
login_manager.login_message_category = 'warning'


@event.listens_for(Engine, 'connect')
def _bat_khoa_ngoai_sqlite(dbapi_conn, _record):
    """SQLite mac dinh tat rang buoc khoa ngoai - bat len de khong xoa nham du lieu dang dung."""
    if isinstance(dbapi_conn, sqlite3.Connection):
        cur = dbapi_conn.cursor()
        cur.execute('PRAGMA foreign_keys=ON')
        cur.close()
