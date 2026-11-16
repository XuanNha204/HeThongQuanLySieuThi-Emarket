"""Tac vu nen: kiem tra canh bao ton kho / cong no dinh ky va sao luu hang ngay."""
import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.extensions import db

log = logging.getLogger('emarket.scheduler')
_scheduler = None


def _chay(app, ham, ten):
    with app.test_request_context():
        try:
            kq = ham()
            db.session.commit()
            log.info('%s: %s', ten, kq)
        except Exception:
            db.session.rollback()
            log.exception('Lỗi tác vụ %s', ten)


def kiem_tra_canh_bao(app):
    from app.services import thongbao
    _chay(app, thongbao.kiem_tra_tat_ca, 'Kiểm tra cảnh báo')


def sao_luu(app):
    from app.services import backup
    _chay(app, backup.sao_luu, 'Sao lưu')


def start(app):
    global _scheduler
    # Khi chay debug co reloader: chi khoi dong trong tien trinh con de khong chay trung 2 lan
    if app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    now = datetime.now()
    _scheduler.add_job(kiem_tra_canh_bao, 'interval', minutes=app.config['KIEM_TRA_CANH_BAO_PHUT'],
                       args=[app], id='canh_bao', next_run_time=now + timedelta(seconds=5))
    _scheduler.add_job(sao_luu, 'cron', hour=app.config['BACKUP_GIO'], minute=0, args=[app], id='sao_luu')

    # Neu lan sao luu gan nhat da qua 24h (vd may tat luc 23h) thi sao luu bu khi khoi dong
    from app.services import backup
    with app.app_context():
        gan_nhat = backup.lan_gan_nhat()
    if gan_nhat is None or now - gan_nhat > timedelta(hours=24):
        _scheduler.add_job(sao_luu, 'date', run_date=now + timedelta(seconds=10), args=[app], id='sao_luu_bu')
    _scheduler.start()
