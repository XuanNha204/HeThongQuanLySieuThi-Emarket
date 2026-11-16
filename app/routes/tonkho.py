"""Nhap hang va ton kho theo tung kho (SD05, SD06, SD14)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user

from app.extensions import db
from app.models import TonKho, HangHoa, Kho, NhaCungCap, PhieuNhap, LoaiHangHoa
from app.services import LoiNghiepVu, tonkho, excel
from app.utils.decorators import quyen_required
from app.utils.helpers import so_thuc, so_nguyen, doc_ngay

bp = Blueprint('tonkho', __name__)


def _truy_van_ton():
    q = TonKho.query.join(HangHoa).join(Kho).filter(HangHoa.trang_thai.is_(True))
    if request.args.get('kho_id', type=int):
        q = q.filter(TonKho.kho_id == request.args.get('kho_id', type=int))
    if request.args.get('loai', type=int):
        q = q.filter(HangHoa.loai_hang_id == request.args.get('loai', type=int))
    if request.args.get('q'):
        tk = request.args['q'].strip()
        q = q.filter(db.or_(HangHoa.ten_hang.ilike(f'%{tk}%'), HangHoa.ma_hang.ilike(f'%{tk}%'),
                            HangHoa.ma_vach == tk))
    ds = q.order_by(Kho.ma_kho, HangHoa.ten_hang).all()
    tinh_trang = request.args.get('tinh_trang')
    if tinh_trang:
        ds = [t for t in ds if t.tinh_trang == tinh_trang]
    return ds


@bp.route('/')
@quyen_required('ton_kho', 'xem')
def index():
    ds = _truy_van_ton()
    if request.args.get('xuat') and current_user.co_quyen('ton_kho', 'in_an'):
        ten_tt = {'thieu': 'Dưới mức tối thiểu', 'vuot': 'Vượt mức tối đa', 'on_dinh': 'Ổn định'}
        return excel.xuat('ton_kho.xlsx', 'BÁO CÁO TỒN KHO',
                          ['Kho', 'Mã hàng', 'Tên hàng', 'ĐVT', 'Tồn', 'Đã bán', 'Tối thiểu', 'Tối đa', 'Tình trạng'],
                          [[t.kho.ten_kho, t.hang_hoa.ma_hang, t.hang_hoa.ten_hang, t.hang_hoa.don_vi_tinh,
                            t.so_luong_ton, t.so_luong_da_ban, t.muc_toi_thieu, t.muc_toi_da, ten_tt[t.tinh_trang]]
                           for t in ds])
    return render_template('tonkho/ton_kho.html', ds=ds, khos=Kho.query.order_by(Kho.ma_kho).all(),
                           loais=LoaiHangHoa.query.order_by(LoaiHangHoa.ten_loai).all(),
                           tong={'ton': sum(t.so_luong_ton for t in ds), 'da_ban': sum(t.so_luong_da_ban for t in ds),
                                 'thieu': sum(t.tinh_trang == 'thieu' for t in ds),
                                 'vuot': sum(t.tinh_trang == 'vuot' for t in ds)})


@bp.route('/<int:id>/nguong', methods=['POST'])
@quyen_required('ton_kho', 'sua')
def cap_nhat_nguong(id):
    tk = db.session.get(TonKho, id) or abort(404)
    toi_thieu, toi_da = so_nguyen(request.form.get('muc_toi_thieu'), -1), so_nguyen(request.form.get('muc_toi_da'), -1)
    if toi_thieu < 0 or toi_da < 0 or (toi_da and toi_da < toi_thieu):
        flash('Mức tối thiểu/tối đa không hợp lệ (tối đa phải ≥ tối thiểu).', 'danger')
    else:
        tk.muc_toi_thieu, tk.muc_toi_da = toi_thieu, toi_da
        tonkho.kiem_tra_canh_bao_ton_kho()
        db.session.commit()
        flash(f'Đã cập nhật ngưỡng tồn cho {tk.hang_hoa.ten_hang} tại {tk.kho.ten_kho}.', 'success')
    return redirect(request.referrer or url_for('tonkho.index'))


# ---------------------------------------------------------------- phieu nhap
@bp.route('/phieu-nhap')
@quyen_required('phieu_nhap', 'xem')
def phieu_nhap():
    q = PhieuNhap.query
    if request.args.get('ncc', type=int):
        q = q.filter_by(nha_cung_cap_id=request.args.get('ncc', type=int))
    if request.args.get('kho_id', type=int):
        q = q.filter_by(kho_id=request.args.get('kho_id', type=int))
    trang = q.order_by(PhieuNhap.ngay_nhap.desc()).paginate(page=request.args.get('page', 1, type=int),
                        per_page=25, error_out=False)
    return render_template('tonkho/phieu_nhap_list.html', trang=trang,
                           nccs=NhaCungCap.query.order_by(NhaCungCap.ten_ncc).all(),
                           khos=Kho.query.order_by(Kho.ma_kho).all())


@bp.route('/phieu-nhap/them', methods=['GET', 'POST'])
@quyen_required('phieu_nhap', 'them')
def them_phieu_nhap():
    if request.method == 'POST':
        f = request.form
        dong = [{'hang_hoa_id': so_nguyen(h), 'so_luong': so_nguyen(sl), 'don_gia': so_thuc(g),
                 'han_su_dung': doc_ngay(hsd)}
                for h, sl, g, hsd in zip(f.getlist('hang_hoa_id'), f.getlist('so_luong'), f.getlist('don_gia'),
                                         f.getlist('han_su_dung'))]
        try:
            pn = tonkho.nhap_hang(current_user, f.get('nha_cung_cap_id', type=int), f.get('kho_id', type=int), dong,
                                  so_thuc(f.get('da_thanh_toan')), doc_ngay(f.get('han_thanh_toan')),
                                  f.get('ghi_chu') or None)
            db.session.commit()
            flash(f'Đã lập phiếu nhập {pn.ma_phieu}, tồn kho {pn.kho.ten_kho} đã được cập nhật.', 'success')
            return redirect(url_for('tonkho.chi_tiet_phieu_nhap', id=pn.id))
        except LoiNghiepVu as e:
            db.session.rollback()
            flash(str(e), 'danger')
    return render_template('tonkho/phieu_nhap_form.html',
                           nccs=NhaCungCap.query.filter_by(trang_thai=True).order_by(NhaCungCap.ten_ncc).all(),
                           khos=Kho.query.filter_by(trang_thai=True).order_by(Kho.ma_kho).all(),
                           hang_hoas=HangHoa.query.filter_by(trang_thai=True).order_by(HangHoa.ten_hang).all())


COT_EXCEL_PN = ['Mã hàng *', 'Số lượng *', 'Đơn giá *', 'Hạn sử dụng']


@bp.route('/phieu-nhap/mau-excel')
@quyen_required('phieu_nhap', 'them')
def mau_excel_phieu_nhap():
    return excel.mau_nhap('mau_phieu_nhap.xlsx', COT_EXCEL_PN, ['HH001', 50, 12000, '31/12/2026'])


@bp.route('/phieu-nhap/nhap-excel', methods=['POST'])
@quyen_required('phieu_nhap', 'them')
def nhap_excel_phieu_nhap():
    """Lap phieu nhap tu file Excel chi tiet hang hoa."""
    try:
        rows = excel.doc(request.files.get('file'), COT_EXCEL_PN)
        dong = []
        for i, r in enumerate(rows, start=2):
            ma = str(int(r['Mã hàng'])) if isinstance(r['Mã hàng'], float) else str(r['Mã hàng'] or '').strip()
            hh = HangHoa.query.filter(db.or_(HangHoa.ma_hang == ma, HangHoa.ma_vach == ma)).first()
            if hh is None:
                raise LoiNghiepVu(f'Dòng {i}: không tìm thấy mã hàng "{ma}".')
            dong.append({'hang_hoa_id': hh.id, 'so_luong': so_nguyen(r['Số lượng']),
                         'don_gia': so_thuc(r['Đơn giá']), 'han_su_dung': doc_ngay(r['Hạn sử dụng'])})
        pn = tonkho.nhap_hang(current_user, request.form.get('nha_cung_cap_id', type=int),
                              request.form.get('kho_id', type=int), dong, so_thuc(request.form.get('da_thanh_toan')))
        db.session.commit()
        flash(f'Đã lập phiếu nhập {pn.ma_phieu} từ Excel ({len(pn.chi_tiets)} mặt hàng).', 'success')
        return redirect(url_for('tonkho.chi_tiet_phieu_nhap', id=pn.id))
    except LoiNghiepVu as e:
        db.session.rollback()
        flash(str(e), 'danger')
        return redirect(url_for('tonkho.them_phieu_nhap'))


@bp.route('/phieu-nhap/<int:id>')
@quyen_required('phieu_nhap', 'xem')
def chi_tiet_phieu_nhap(id):
    pn = db.session.get(PhieuNhap, id) or abort(404)
    return render_template('tonkho/phieu_nhap_chi_tiet.html', pn=pn)
