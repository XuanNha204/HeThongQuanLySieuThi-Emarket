from datetime import datetime, date

from app.extensions import db

LOAI_CHUNG_TU = {'hoa_don': 'Hóa đơn bán hàng', 'phieu_nhap': 'Phiếu nhập kho', 'dau_ky': 'Nợ đầu kỳ'}


class CongNo(db.Model):
    """Cong no theo tung chung tu - cua khach hang (phai thu) hoac nha cung cap (phai tra)."""
    __tablename__ = 'cong_no'
    id = db.Column(db.Integer, primary_key=True)
    doi_tuong = db.Column(db.String(20), nullable=False)  # khach_hang / nha_cung_cap
    khach_hang_id = db.Column(db.Integer, db.ForeignKey('khach_hang.id'))
    nha_cung_cap_id = db.Column(db.Integer, db.ForeignKey('nha_cung_cap.id'))
    loai_chung_tu = db.Column(db.String(20), nullable=False)
    ma_chung_tu = db.Column(db.String(30), nullable=False)
    ngay_phat_sinh = db.Column(db.Date, default=date.today)
    han_thanh_toan = db.Column(db.Date)
    so_tien = db.Column(db.Float, nullable=False)
    da_thanh_toan = db.Column(db.Float, default=0)
    ghi_chu = db.Column(db.String(300))

    khach_hang = db.relationship('KhachHang', backref='cong_nos')
    nha_cung_cap = db.relationship('NhaCungCap', backref='cong_nos')
    thanh_toans = db.relationship('ThanhToanCongNo', backref='cong_no', cascade='all, delete-orphan',
                                  order_by='ThanhToanCongNo.ngay')

    @property
    def con_lai(self):
        return round((self.so_tien or 0) - (self.da_thanh_toan or 0), 2)

    @property
    def ten_doi_tuong(self):
        return self.khach_hang.ho_ten if self.doi_tuong == 'khach_hang' else self.nha_cung_cap.ten_ncc

    @property
    def ten_loai_chung_tu(self):
        return LOAI_CHUNG_TU.get(self.loai_chung_tu, self.loai_chung_tu)

    @property
    def qua_han(self):
        return self.con_lai > 0 and self.han_thanh_toan is not None and self.han_thanh_toan < date.today()

    @property
    def so_ngay_qua_han(self):
        return (date.today() - self.han_thanh_toan).days if self.qua_han else 0

    @property
    def trang_thai(self):
        if self.con_lai <= 0:
            return ('Đã tất toán', 'success')
        if self.qua_han:
            return ('Quá hạn', 'danger')
        if self.da_thanh_toan:
            return ('Trả một phần', 'warning')
        return ('Chưa trả', 'secondary')


class ThanhToanCongNo(db.Model):
    __tablename__ = 'thanh_toan_cong_no'
    id = db.Column(db.Integer, primary_key=True)
    cong_no_id = db.Column(db.Integer, db.ForeignKey('cong_no.id'), nullable=False)
    ngay = db.Column(db.DateTime, default=datetime.now)
    so_tien = db.Column(db.Float, nullable=False)
    hinh_thuc = db.Column(db.String(20), default='tien_mat')
    nguoi_thuc_hien_id = db.Column(db.Integer, db.ForeignKey('nguoi_dung.id'))
    ghi_chu = db.Column(db.String(200))

    nguoi_thuc_hien = db.relationship('NguoiDung')
