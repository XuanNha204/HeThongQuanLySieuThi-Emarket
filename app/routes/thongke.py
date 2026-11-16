"""In an / thong ke theo ngay, thang, nam, hang hoa, nha cung cap (SD08)."""
from datetime import date, timedelta

from flask import Blueprint, render_template, request
from flask_login import current_user

from app.services import thongke, excel
from app.utils.decorators import quyen_required
from app.utils.helpers import doc_ngay

bp = Blueprint('thongke', __name__)

LOAI_BAO_CAO = {
    'ngay': 'Doanh thu theo ngày',
    'thang': 'Doanh thu theo tháng',
    'nam': 'Doanh thu theo năm',
    'hang_hoa': 'Theo hàng hóa',
    'ncc': 'Theo nhà cung cấp',
}


def _mac_dinh_tu(loai, den):
    if loai == 'thang':
        return date(den.year, 1, 1)
    if loai == 'nam':
        return date(den.year - 4, 1, 1)
    return den - timedelta(days=29)


@bp.route('/')
@quyen_required('bao_cao', 'xem')
def index():
    loai = request.args.get('loai', 'ngay')
    if loai not in LOAI_BAO_CAO:
        loai = 'ngay'
    den = doc_ngay(request.args.get('den')) or date.today()
    tu = doc_ngay(request.args.get('tu')) or _mac_dinh_tu(loai, den)
    if tu > den:
        tu, den = den, tu

    if loai in thongke.KY:
        dl = thongke.doanh_thu_theo_ky(loai, tu, den)
        cot = [(thongke.KY[loai][1], 'ky', None), ('Số hóa đơn', 'so_hoa_don', 'so'),
               ('Doanh thu', 'doanh_thu', 'vnd'), ('Giá vốn', 'gia_von', 'vnd'), ('Lợi nhuận', 'loi_nhuan', 'vnd')]
        bieu_do = {'nhan': [d['ky'] for d in dl], 'doanh_thu': [d['doanh_thu'] for d in dl],
                   'loi_nhuan': [d['loi_nhuan'] for d in dl]}
    elif loai == 'hang_hoa':
        dl = thongke.theo_hang_hoa(tu, den)
        cot = [('Mã hàng', 'ma', None), ('Tên hàng', 'ten', None), ('ĐVT', 'dvt', None),
               ('SL bán', 'so_luong', 'so'), ('Doanh thu', 'doanh_thu', 'vnd'), ('Lợi nhuận', 'loi_nhuan', 'vnd'),
               ('Tồn hiện tại', 'ton', 'so')]
        top = dl[:10]
        bieu_do = {'nhan': [d['ten'] for d in top], 'doanh_thu': [d['doanh_thu'] for d in top],
                   'loi_nhuan': [d['loi_nhuan'] for d in top]}
    else:
        dl = thongke.theo_nha_cung_cap(tu, den)
        cot = [('Mã NCC', 'ma', None), ('Nhà cung cấp', 'ten', None), ('Số mặt hàng', 'so_mat_hang', 'so'),
               ('Tiền nhập', 'tien_nhap', 'vnd'), ('Doanh thu hàng bán', 'doanh_thu', 'vnd'),
               ('Còn nợ NCC', 'con_no', 'vnd')]
        bieu_do = {'nhan': [d['ten'] for d in dl], 'doanh_thu': [d['doanh_thu'] for d in dl],
                   'tien_nhap': [d['tien_nhap'] for d in dl]}

    tong = {k: sum(d[k] for d in dl) for _, k, f in cot if f in ('vnd', 'so') and k != 'ton'}
    tieu_de = f'{LOAI_BAO_CAO[loai].upper()} TỪ {tu:%d/%m/%Y} ĐẾN {den:%d/%m/%Y}'
    if request.args.get('xuat') and current_user.co_quyen('bao_cao', 'in_an'):
        return excel.xuat(f'thong_ke_{loai}_{tu:%Y%m%d}_{den:%Y%m%d}.xlsx', tieu_de, [c[0] for c in cot],
                          [[d[c[1]] for c in cot] for d in dl],
                          tong=['Tổng cộng'] + [tong.get(c[1], '') for c in cot[1:]])
    return render_template('thongke/index.html', loai=loai, LOAI=LOAI_BAO_CAO, tu=tu, den=den, dl=dl, cot=cot,
                           tong=tong, bieu_do=bieu_do, tieu_de=tieu_de)
