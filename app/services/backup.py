"""Sao luu du lieu hang ngay (SQLite online backup API)."""
import os
import sqlite3
from datetime import datetime

from flask import current_app

from app.extensions import db


def _thu_muc():
    d = current_app.config['BACKUP_DIR']
    os.makedirs(d, exist_ok=True)
    return d


def _duong_dan_db():
    return db.engine.url.database


def sao_luu():
    """Tao ban sao luu moi, giu lai N ban gan nhat. Tra ve ten file."""
    nguon = _duong_dan_db()
    if not nguon or nguon == ':memory:':
        raise RuntimeError('Chỉ hỗ trợ sao lưu CSDL SQLite dạng file.')
    ten = f'emarket_{datetime.now():%Y%m%d_%H%M%S}.db'
    dich = os.path.join(_thu_muc(), ten)
    src = sqlite3.connect(nguon)
    dst = sqlite3.connect(dich)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    _don_dep()
    return ten


def danh_sach():
    d = _thu_muc()
    ket_qua = []
    for ten in sorted(os.listdir(d), reverse=True):
        if ten.startswith('emarket_') and ten.endswith('.db'):
            p = os.path.join(d, ten)
            ket_qua.append({'ten': ten, 'kich_thuoc': os.path.getsize(p),
                            'thoi_gian': datetime.fromtimestamp(os.path.getmtime(p))})
    return ket_qua


def lan_gan_nhat():
    ds = danh_sach()
    return ds[0]['thoi_gian'] if ds else None


def duong_dan(ten):
    ten = os.path.basename(ten)
    p = os.path.join(_thu_muc(), ten)
    return p if ten.startswith('emarket_') and ten.endswith('.db') and os.path.isfile(p) else None


def _don_dep():
    giu = current_app.config['BACKUP_GIU_LAI']
    for f in danh_sach()[giu:]:
        os.remove(os.path.join(_thu_muc(), f['ten']))
