from datetime import datetime

from app.extensions import db


class TonKho(db.Model):
    """So luong ton va da ban cua 1 mat hang tren 1 kho."""
    __tablename__ = 'ton_kho'
    id = db.Column(db.Integer, primary_key=True)
    hang_hoa_id = db.Column(db.Integer, db.ForeignKey('hang_hoa.id'), nullable=False)
    kho_id = db.Column(db.Integer, db.ForeignKey('kho.id'), nullable=False)
    so_luong_ton = db.Column(db.Integer, default=0)
    so_luong_da_ban = db.Column(db.Integer, default=0)
    muc_toi_thieu = db.Column(db.Integer, default=10)
    muc_toi_da = db.Column(db.Integer, default=1000)

    __table_args__ = (db.UniqueConstraint('hang_hoa_id', 'kho_id'),)

    @property
    def tinh_trang(self):
        if self.so_luong_ton < self.muc_toi_thieu:
            return 'thieu'
        if self.muc_toi_da and self.so_luong_ton > self.muc_toi_da:
            return 'vuot'
        return 'on_dinh'


class PhieuNhap(db.Model):
    """Chung tu nhap hang tu nha cung cap vao 1 kho."""
    __tablename__ = 'phieu_nhap'
    id = db.Column(db.Integer, primary_key=True)
    ma_phieu = db.Column(db.String(30), unique=True, nullable=False)
    nha_cung_cap_id = db.Column(db.Integer, db.ForeignKey('nha_cung_cap.id'), nullable=False)
    kho_id = db.Column(db.Integer, db.ForeignKey('kho.id'), nullable=False)
    nguoi_nhap_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    ngay_nhap = db.Column(db.DateTime, default=datetime.now)
    tong_tien = db.Column(db.Float, default=0)
    da_thanh_toan = db.Column(db.Float, default=0)
    ghi_chu = db.Column(db.String(300))

    nha_cung_cap = db.relationship('NhaCungCap', backref='phieu_nhaps')
    kho = db.relationship('Kho')
    nguoi_nhap = db.relationship('NguoiDung')
    chi_tiets = db.relationship('ChiTietPhieuNhap', backref='phieu_nhap', cascade='all, delete-orphan')


class ChiTietPhieuNhap(db.Model):
    __tablename__ = 'chi_tiet_phieu_nhap'
    id = db.Column(db.Integer, primary_key=True)
    phieu_nhap_id = db.Column(db.Integer, db.ForeignKey('phieu_nhap.id'), nullable=False)
    hang_hoa_id = db.Column(db.Integer, db.ForeignKey('hang_hoa.id'), nullable=False)
    so_luong = db.Column(db.Integer, nullable=False)
    don_gia = db.Column(db.Float, nullable=False)
    thanh_tien = db.Column(db.Float, nullable=False)
    han_su_dung = db.Column(db.Date)

    hang_hoa = db.relationship('HangHoa')
