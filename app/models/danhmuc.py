from datetime import datetime, date

from app.extensions import db


class NhaCungCap(db.Model):
    __tablename__ = 'nha_cung_cap'
    id = db.Column(db.Integer, primary_key=True)
    ma_ncc = db.Column(db.String(20), unique=True, nullable=False)
    ten_ncc = db.Column(db.String(200), nullable=False)
    dia_chi = db.Column(db.String(300))
    dien_thoai = db.Column(db.String(20))
    email = db.Column(db.String(120))
    nguoi_lien_he = db.Column(db.String(100))
    ma_so_thue = db.Column(db.String(20))
    trang_thai = db.Column(db.Boolean, default=True)

    hang_hoas = db.relationship('HangHoa', backref='nha_cung_cap')

    def __str__(self):
        return self.ten_ncc


class LoaiHangHoa(db.Model):
    __tablename__ = 'loai_hang_hoa'
    id = db.Column(db.Integer, primary_key=True)
    ma_loai = db.Column(db.String(20), unique=True, nullable=False)
    ten_loai = db.Column(db.String(100), nullable=False)
    mo_ta = db.Column(db.String(300))

    hang_hoas = db.relationship('HangHoa', backref='loai_hang')

    def __str__(self):
        return self.ten_loai


class HangHoa(db.Model):
    __tablename__ = 'hang_hoa'
    id = db.Column(db.Integer, primary_key=True)
    ma_hang = db.Column(db.String(30), unique=True, nullable=False)
    ma_vach = db.Column(db.String(50), unique=True)
    chuan_ma_vach = db.Column(db.String(20), default='ean13')
    ten_hang = db.Column(db.String(200), nullable=False)
    loai_hang_id = db.Column(db.Integer, db.ForeignKey('loai_hang_hoa.id'))
    nha_cung_cap_id = db.Column(db.Integer, db.ForeignKey('nha_cung_cap.id'))
    don_vi_tinh = db.Column(db.String(20), default='Cái')
    gia_nhap = db.Column(db.Float, default=0)
    gia_ban = db.Column(db.Float, default=0)
    han_su_dung = db.Column(db.Date)
    xuat_xu = db.Column(db.String(100))
    mo_ta = db.Column(db.Text)
    trang_thai = db.Column(db.Boolean, default=True)  # dang kinh doanh / ngung ban
    ngay_tao = db.Column(db.DateTime, default=datetime.now)

    ton_khos = db.relationship('TonKho', backref='hang_hoa', cascade='all, delete-orphan')

    def __str__(self):
        return f'{self.ma_hang} - {self.ten_hang}'

    @property
    def tong_ton(self):
        return sum(t.so_luong_ton for t in self.ton_khos)

    @property
    def tong_da_ban(self):
        return sum(t.so_luong_da_ban for t in self.ton_khos)

    def ton_tai_kho(self, kho_id):
        for t in self.ton_khos:
            if t.kho_id == kho_id:
                return t.so_luong_ton
        return 0

    @property
    def so_ngay_con_han(self):
        if not self.han_su_dung:
            return None
        return (self.han_su_dung - date.today()).days


class LoaiKhachHang(db.Model):
    __tablename__ = 'loai_khach_hang'
    id = db.Column(db.Integer, primary_key=True)
    ma_loai = db.Column(db.String(20), unique=True, nullable=False)
    ten_loai = db.Column(db.String(100), nullable=False)
    chiet_khau = db.Column(db.Float, default=0)      # % giam tren gia niem yet
    han_muc_no = db.Column(db.Float, default=0)      # muc no toi da cho phep (0 = dung mac dinh)
    so_ngay_no = db.Column(db.Integer, default=0)    # thoi gian no toi da (0 = dung mac dinh)
    mo_ta = db.Column(db.String(300))

    khach_hangs = db.relationship('KhachHang', backref='loai_khach_hang')

    def __str__(self):
        return self.ten_loai


class Kho(db.Model):
    __tablename__ = 'kho'
    id = db.Column(db.Integer, primary_key=True)
    ma_kho = db.Column(db.String(20), unique=True, nullable=False)
    ten_kho = db.Column(db.String(100), nullable=False)
    dia_chi = db.Column(db.String(300))
    trang_thai = db.Column(db.Boolean, default=True)

    ton_khos = db.relationship('TonKho', backref='kho')

    def __str__(self):
        return self.ten_kho
