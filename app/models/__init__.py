from app.extensions import db, login_manager
from app.models.nguoidung import NguoiDung, PhanQuyen, CHUC_NANG, QUYEN, VAI_TRO
from app.models.danhmuc import NhaCungCap, LoaiHangHoa, HangHoa, LoaiKhachHang, Kho
from app.models.khachhang import KhachHang, TheThanhThiet, LichSuDiem
from app.models.banhang import (GiaBanTheoKH, DonHang, ChiTietDonHang, LichSuDonHang, HoaDon,
                                TRANG_THAI_DON, HINH_THUC_TT)
from app.models.tonkho import TonKho, PhieuNhap, ChiTietPhieuNhap
from app.models.congno import CongNo, ThanhToanCongNo
from app.models.thongbao import ThongBao, LOAI_THONG_BAO


@login_manager.user_loader
def load_user(user_id):
    """Hai loai tai khoan: nhan vien (nv-<id>) va khach hang (kh-<id>)."""
    loai, _, pk = user_id.partition('-')
    if not pk.isdigit():
        return None
    model = {'nv': NguoiDung, 'kh': KhachHang}.get(loai)
    return db.session.get(model, int(pk)) if model else None
