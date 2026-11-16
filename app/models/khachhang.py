from datetime import datetime

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class KhachHang(UserMixin, db.Model):
    """Khach hang - dong thoi la tai khoan dang nhap cong dat hang online."""
    __tablename__ = 'khach_hang'
    id = db.Column(db.Integer, primary_key=True)
    ma_kh = db.Column(db.String(20), unique=True, nullable=False)
    ho_ten = db.Column(db.String(100), nullable=False)
    dien_thoai = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120))
    dia_chi = db.Column(db.String(300))
    loai_kh_id = db.Column(db.Integer, db.ForeignKey('loai_khach_hang.id'))
    han_muc_no = db.Column(db.Float)          # rieng cho KH; bo trong = theo loai KH
    tong_mua = db.Column(db.Float, default=0)
    diem_tich_luy = db.Column(db.Integer, default=0)
    mat_khau_hash = db.Column(db.String(256))
    trang_thai = db.Column(db.Boolean, default=True)
    ngay_tao = db.Column(db.DateTime, default=datetime.now)

    the_than_thiet = db.relationship('TheThanhThiet', backref='khach_hang', uselist=False,
                                     cascade='all, delete-orphan')
    lich_su_diem = db.relationship('LichSuDiem', backref='khach_hang', cascade='all, delete-orphan',
                                   order_by='LichSuDiem.ngay.desc()')
    don_hangs = db.relationship('DonHang', backref='khach_hang', order_by='DonHang.ngay_dat.desc()')

    def __str__(self):
        return f'{self.ma_kh} - {self.ho_ten}'

    def get_id(self):
        return f'kh-{self.id}'

    @property
    def is_active(self):
        return bool(self.trang_thai)

    def set_password(self, pw):
        self.mat_khau_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return bool(self.mat_khau_hash) and check_password_hash(self.mat_khau_hash, pw)

    @property
    def co_the(self):
        return self.the_than_thiet is not None and self.the_than_thiet.trang_thai

    @property
    def han_muc_no_ap_dung(self):
        if self.han_muc_no:
            return self.han_muc_no
        if self.loai_khach_hang and self.loai_khach_hang.han_muc_no:
            return self.loai_khach_hang.han_muc_no
        return current_app.config['HAN_MUC_NO_MAC_DINH']

    @property
    def so_ngay_no_ap_dung(self):
        if self.loai_khach_hang and self.loai_khach_hang.so_ngay_no:
            return self.loai_khach_hang.so_ngay_no
        return current_app.config['SO_NGAY_NO_MAC_DINH']


class TheThanhThiet(db.Model):
    __tablename__ = 'the_than_thiet'
    id = db.Column(db.Integer, primary_key=True)
    ma_the = db.Column(db.String(30), unique=True, nullable=False)
    khach_hang_id = db.Column(db.Integer, db.ForeignKey('khach_hang.id'), unique=True, nullable=False)
    ngay_lap = db.Column(db.DateTime, default=datetime.now)
    chung_tu_dat_dieu_kien = db.Column(db.String(30))  # ma hoa don dat nguong
    gia_tri_dat_dieu_kien = db.Column(db.Float)
    trang_thai = db.Column(db.Boolean, default=True)


class LichSuDiem(db.Model):
    """Bien dong diem: tich luy (+) khi mua, quy doi (-) khi dung diem thanh toan."""
    __tablename__ = 'lich_su_diem'
    id = db.Column(db.Integer, primary_key=True)
    khach_hang_id = db.Column(db.Integer, db.ForeignKey('khach_hang.id'), nullable=False)
    so_diem = db.Column(db.Integer, nullable=False)
    loai = db.Column(db.String(20), nullable=False)  # tich_luy / quy_doi / dieu_chinh
    chung_tu = db.Column(db.String(30))
    mo_ta = db.Column(db.String(200))
    ngay = db.Column(db.DateTime, default=datetime.now)
