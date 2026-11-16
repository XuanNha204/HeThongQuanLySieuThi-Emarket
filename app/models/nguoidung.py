from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

# Danh sach chuc nang / chung tu duoc phan quyen chi tiet
CHUC_NANG = {
    'danh_muc': 'Danh mục (NCC, hàng hóa, loại KH, kho)',
    'khach_hang': 'Khách hàng, thẻ thân thiết, điểm',
    'gia_ban': 'Giá bán theo khách hàng',
    'don_hang': 'Chứng từ: Đơn đặt hàng',
    'hoa_don': 'Chứng từ: Hóa đơn bán hàng (POS)',
    'phieu_nhap': 'Chứng từ: Phiếu nhập kho',
    'ton_kho': 'Tồn kho',
    'cong_no': 'Chứng từ: Công nợ',
    'bao_cao': 'Báo cáo thống kê',
    'he_thong': 'Hệ thống (người dùng, phân quyền, sao lưu)',
}
QUYEN = {'xem': 'Xem', 'them': 'Thêm', 'sua': 'Sửa', 'xoa': 'Xóa', 'in_an': 'In / Xuất'}

VAI_TRO = {
    'admin': 'Quản trị viên',
    'quan_ly': 'Quản lý',
    'ban_hang': 'Nhân viên bán hàng',
    'kho': 'Nhân viên kho',
}

# Quyen mac dinh khi tao nguoi dung theo vai tro (co the chinh lai tung nguoi)
_TAT_CA = set(QUYEN)
QUYEN_MAC_DINH = {
    'quan_ly': {cn: _TAT_CA for cn in CHUC_NANG if cn != 'he_thong'},
    'ban_hang': {
        'danh_muc': {'xem'}, 'khach_hang': {'xem', 'them', 'sua'}, 'gia_ban': {'xem'},
        'don_hang': {'xem', 'them', 'sua', 'in_an'}, 'hoa_don': {'xem', 'them', 'in_an'},
        'ton_kho': {'xem'}, 'cong_no': {'xem'},
    },
    'kho': {
        'danh_muc': {'xem', 'them', 'sua'}, 'phieu_nhap': {'xem', 'them', 'in_an'},
        'ton_kho': {'xem', 'sua', 'in_an'}, 'cong_no': {'xem'},
    },
}


class NguoiDung(UserMixin, db.Model):
    """Nhan vien / quan ly su dung he thong."""
    __tablename__ = 'nguoi_dung'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    ho_ten = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    dien_thoai = db.Column(db.String(20))
    vai_tro = db.Column(db.String(20), default='ban_hang')
    trang_thai = db.Column(db.Boolean, default=True)
    ngay_tao = db.Column(db.DateTime, default=datetime.now)

    phan_quyens = db.relationship('PhanQuyen', backref='nguoi_dung', cascade='all, delete-orphan')

    def get_id(self):
        return f'nv-{self.id}'

    @property
    def is_active(self):
        return bool(self.trang_thai)

    @property
    def is_admin(self):
        return self.vai_tro == 'admin'

    @property
    def ten_vai_tro(self):
        return VAI_TRO.get(self.vai_tro, self.vai_tro)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def co_quyen(self, chuc_nang, quyen='xem'):
        if self.is_admin:
            return True
        for pq in self.phan_quyens:
            if pq.chuc_nang == chuc_nang:
                return bool(getattr(pq, quyen, False))
        return False

    def ap_quyen_mac_dinh(self):
        """Gan bo quyen mau theo vai tro."""
        self.phan_quyens = []
        for cn, qs in QUYEN_MAC_DINH.get(self.vai_tro, {}).items():
            self.phan_quyens.append(PhanQuyen(chuc_nang=cn, **{q: q in qs for q in QUYEN}))


class PhanQuyen(db.Model):
    """Quyen cua 1 nguoi dung tren 1 chuc nang / chung tu."""
    __tablename__ = 'phan_quyen'
    id = db.Column(db.Integer, primary_key=True)
    nguoi_dung_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'), nullable=False)
    chuc_nang = db.Column(db.String(50), nullable=False)
    xem = db.Column(db.Boolean, default=False)
    them = db.Column(db.Boolean, default=False)
    sua = db.Column(db.Boolean, default=False)
    xoa = db.Column(db.Boolean, default=False)
    in_an = db.Column(db.Boolean, default=False)

    __table_args__ = (db.UniqueConstraint('nguoi_dung_id', 'chuc_nang'),)
