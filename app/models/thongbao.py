from datetime import datetime

from app.extensions import db

LOAI_THONG_BAO = {
    'ton_kho_thieu': ('Tồn kho dưới mức tối thiểu', 'warning', 'bi-box-seam'),
    'ton_kho_vuot': ('Tồn kho vượt mức tối đa', 'info', 'bi-boxes'),
    'no_qua_han': ('Khách hàng nợ quá hạn', 'danger', 'bi-alarm'),
    'no_vuot_muc': ('Khách hàng nợ vượt mức cho phép', 'danger', 'bi-exclamation-octagon'),
}


class ThongBao(db.Model):
    """Canh bao tu dong. Moi 'khoa' chi co 1 canh bao dang hieu luc (tranh trung lap)."""
    __tablename__ = 'thong_bao'
    id = db.Column(db.Integer, primary_key=True)
    loai = db.Column(db.String(30), nullable=False)
    khoa = db.Column(db.String(100), nullable=False, index=True)
    noi_dung = db.Column(db.String(500), nullable=False)
    lien_ket = db.Column(db.String(200))
    ngay_tao = db.Column(db.DateTime, default=datetime.now)
    da_doc = db.Column(db.Boolean, default=False)
    da_xu_ly = db.Column(db.Boolean, default=False)   # dieu kien canh bao khong con
    ngay_xu_ly = db.Column(db.DateTime)

    @property
    def thong_tin_loai(self):
        return LOAI_THONG_BAO.get(self.loai, (self.loai, 'secondary', 'bi-bell'))
