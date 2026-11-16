from datetime import datetime

from app.extensions import db

TRANG_THAI_DON = {
    'cho_xu_ly': ('Chờ xử lý', 'secondary'),
    'dang_xu_ly': ('Đang xử lý', 'info'),
    'dang_giao': ('Đang giao', 'primary'),
    'hoan_thanh': ('Hoàn thành', 'success'),
    'da_huy': ('Đã hủy', 'danger'),
}
# Luong xu ly don hang hop le
CHUYEN_TRANG_THAI = {
    'cho_xu_ly': ['dang_xu_ly', 'da_huy'],
    'dang_xu_ly': ['dang_giao', 'hoan_thanh', 'da_huy'],
    'dang_giao': ['hoan_thanh', 'da_huy'],
    'hoan_thanh': [],
    'da_huy': [],
}
HINH_THUC_TT = {
    'tien_mat': 'Tiền mặt',
    'the': 'Thẻ ngân hàng',
    'chuyen_khoan': 'Chuyển khoản',
    'ghi_no': 'Ghi nợ (công nợ)',
}


class GiaBanTheoKH(db.Model):
    """Gia ban ap rieng cho tung khach hang theo tung mat hang."""
    __tablename__ = 'gia_ban_theo_kh'
    id = db.Column(db.Integer, primary_key=True)
    khach_hang_id = db.Column(db.Integer, db.ForeignKey('khach_hang.id'), nullable=False)
    hang_hoa_id = db.Column(db.Integer, db.ForeignKey('hang_hoa.id'), nullable=False)
    gia_ban = db.Column(db.Float, nullable=False)
    ngay_ap_dung = db.Column(db.DateTime, default=datetime.now)
    ghi_chu = db.Column(db.String(200))

    khach_hang = db.relationship('KhachHang', backref=db.backref('gia_ban_riengs', cascade='all, delete-orphan'))
    hang_hoa = db.relationship('HangHoa', backref=db.backref('gia_ban_riengs', cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('khach_hang_id', 'hang_hoa_id'),)


class DonHang(db.Model):
    """Don hang: dat online boi khach hang hoac ban tai quay (POS)."""
    __tablename__ = 'don_hang'
    id = db.Column(db.Integer, primary_key=True)
    ma_don = db.Column(db.String(30), unique=True, nullable=False)
    khach_hang_id = db.Column(db.Integer, db.ForeignKey('khach_hang.id'))
    kho_id = db.Column(db.Integer, db.ForeignKey('kho.id'), nullable=False)
    nguon = db.Column(db.String(20), default='online')  # online / tai_quay
    trang_thai = db.Column(db.String(20), default='cho_xu_ly')
    ngay_dat = db.Column(db.DateTime, default=datetime.now)
    tong_tien_hang = db.Column(db.Float, default=0)
    diem_su_dung = db.Column(db.Integer, default=0)
    giam_gia_diem = db.Column(db.Float, default=0)
    tong_thanh_toan = db.Column(db.Float, default=0)
    diem_cong = db.Column(db.Integer, default=0)
    dia_chi_giao = db.Column(db.String(300))
    ghi_chu = db.Column(db.String(300))
    nguoi_xu_ly_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))

    kho = db.relationship('Kho')
    nguoi_xu_ly = db.relationship('NguoiDung')
    chi_tiets = db.relationship('ChiTietDonHang', backref='don_hang', cascade='all, delete-orphan')
    lich_sus = db.relationship('LichSuDonHang', backref='don_hang', cascade='all, delete-orphan',
                               order_by='LichSuDonHang.thoi_gian')
    hoa_don = db.relationship('HoaDon', backref='don_hang', uselist=False)

    @property
    def ten_trang_thai(self):
        return TRANG_THAI_DON[self.trang_thai][0]

    @property
    def mau_trang_thai(self):
        return TRANG_THAI_DON[self.trang_thai][1]

    @property
    def trang_thai_tiep(self):
        return CHUYEN_TRANG_THAI[self.trang_thai]


class ChiTietDonHang(db.Model):
    __tablename__ = 'chi_tiet_don_hang'
    id = db.Column(db.Integer, primary_key=True)
    don_hang_id = db.Column(db.Integer, db.ForeignKey('don_hang.id'), nullable=False)
    hang_hoa_id = db.Column(db.Integer, db.ForeignKey('hang_hoa.id'), nullable=False)
    so_luong = db.Column(db.Integer, nullable=False)
    don_gia = db.Column(db.Float, nullable=False)       # gia da ap theo khach hang
    gia_niem_yet = db.Column(db.Float)                  # gia ban chung tai thoi diem ban
    gia_von = db.Column(db.Float, default=0)            # gia nhap tai thoi diem ban
    thanh_tien = db.Column(db.Float, nullable=False)

    hang_hoa = db.relationship('HangHoa')


class LichSuDonHang(db.Model):
    """Theo doi qua trinh xu ly don hang."""
    __tablename__ = 'lich_su_don_hang'
    id = db.Column(db.Integer, primary_key=True)
    don_hang_id = db.Column(db.Integer, db.ForeignKey('don_hang.id'), nullable=False)
    trang_thai = db.Column(db.String(20), nullable=False)
    thoi_gian = db.Column(db.DateTime, default=datetime.now)
    nguoi_thuc_hien = db.Column(db.String(100))
    ghi_chu = db.Column(db.String(300))

    @property
    def ten_trang_thai(self):
        return TRANG_THAI_DON[self.trang_thai][0]


class HoaDon(db.Model):
    """Chung tu ban hang - lap khi don hang hoan thanh (thanh toan)."""
    __tablename__ = 'hoa_don'
    id = db.Column(db.Integer, primary_key=True)
    ma_hd = db.Column(db.String(30), unique=True, nullable=False)
    don_hang_id = db.Column(db.Integer, db.ForeignKey('don_hang.id'), unique=True, nullable=False)
    nhan_vien_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    ngay_lap = db.Column(db.DateTime, default=datetime.now)
    tong_tien = db.Column(db.Float, default=0)
    hinh_thuc_tt = db.Column(db.String(20), default='tien_mat')
    tien_khach_dua = db.Column(db.Float, default=0)

    nhan_vien = db.relationship('NguoiDung')

    @property
    def ten_hinh_thuc(self):
        return HINH_THUC_TT.get(self.hinh_thuc_tt, self.hinh_thuc_tt)
