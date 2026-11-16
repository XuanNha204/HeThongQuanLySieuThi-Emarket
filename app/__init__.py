import os

from flask import Flask, redirect, url_for
from flask_login import current_user

from config import Config
from app.extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401  (dang ky cac bang)
    from app.utils import filters
    filters.register(app)

    from app.routes import auth, dashboard, danhmuc, khachhang, banhang, tonkho, congno, thongke, hethong, kiosk, portal
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(danhmuc.bp, url_prefix='/danh-muc')
    app.register_blueprint(khachhang.bp, url_prefix='/khach-hang')
    app.register_blueprint(banhang.bp, url_prefix='/ban-hang')
    app.register_blueprint(tonkho.bp, url_prefix='/ton-kho')
    app.register_blueprint(congno.bp, url_prefix='/cong-no')
    app.register_blueprint(thongke.bp, url_prefix='/thong-ke')
    app.register_blueprint(hethong.bp, url_prefix='/he-thong')
    app.register_blueprint(kiosk.bp, url_prefix='/kiosk')
    app.register_blueprint(portal.bp, url_prefix='/khach')

    @app.context_processor
    def inject_globals():
        from app.models import ThongBao, NguoiDung
        so_thong_bao = 0
        if current_user.is_authenticated and isinstance(current_user, NguoiDung):
            so_thong_bao = ThongBao.query.filter_by(da_xu_ly=False, da_doc=False).count()
        return dict(so_thong_bao=so_thong_bao, cfg=app.config)

    with app.app_context():
        db.create_all()

    if app.config.get('SCHEDULER_ENABLED'):
        from app.services import scheduler
        scheduler.start(app)

    return app
