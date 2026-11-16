"""Cong no khach hang / nha cung cap theo chung tu (SD07, SD13)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user

from app.extensions import db
from app.models import CongNo, KhachHang, NhaCungCap, HINH_THUC_TT
from app.services import LoiNghiepVu, congno, excel
from app.utils.decorators import quyen_required
from app.utils.helpers import so_thuc

bp = Blueprint('congno', __name__)


@bp.route('/')
@quyen_required('cong_no', 'xem')
def danh_sach():
    doi_tuong = request.args.get('doi_tuong', 'khach_hang')
    if doi_tuong not in ('khach_hang', 'nha_cung_cap'):
        doi_tuong = 'khach_hang'
    q = CongNo.query.filter_by(doi_tuong=doi_tuong)
    if request.args.get('khach_hang_id', type=int):
        q = q.filter_by(khach_hang_id=request.args.get('khach_hang_id', type=int))
    if request.args.get('nha_cung_cap_id', type=int):
        q = q.filter_by(nha_cung_cap_id=request.args.get('nha_cung_cap_id', type=int))
    if request.args.get('q'):
        q = q.filter(CongNo.ma_chung_tu.ilike(f"%{request.args['q']}%"))
    ds = q.order_by(CongNo.han_thanh_toan).all()
    loc = request.args.get('trang_thai', 'con_no')
    if loc == 'con_no':
        ds = [c for c in ds if c.con_lai > 0]
    elif loc == 'qua_han':
        ds = [c for c in ds if c.qua_han]
    elif loc == 'tat_toan':
        ds = [c for c in ds if c.con_lai <= 0]
    if request.args.get('xuat') and current_user.co_quyen('cong_no', 'in_an'):
        return excel.xuat(f'cong_no_{doi_tuong}.xlsx',
                          'CÔNG NỢ ' + ('KHÁCH HÀNG' if doi_tuong == 'khach_hang' else 'NHÀ CUNG CẤP'),
                          ['Đối tượng', 'Loại chứng từ', 'Mã chứng từ', 'Ngày phát sinh', 'Hạn thanh toán',
                           'Số tiền', 'Đã thanh toán', 'Còn lại', 'Trạng thái'],
                          [[c.ten_doi_tuong, c.ten_loai_chung_tu, c.ma_chung_tu, c.ngay_phat_sinh, c.han_thanh_toan,
                            c.so_tien, c.da_thanh_toan, c.con_lai, c.trang_thai[0]] for c in ds],
                          tong=['Tổng', '', '', '', '', sum(c.so_tien for c in ds),
                                sum(c.da_thanh_toan or 0 for c in ds), sum(c.con_lai for c in ds), ''])
    return render_template('congno/danh_sach.html', ds=ds, doi_tuong=doi_tuong, loc=loc,
                           tong_con_lai=sum(c.con_lai for c in ds),
                           khach_hangs=KhachHang.query.order_by(KhachHang.ho_ten).all(),
                           nccs=NhaCungCap.query.order_by(NhaCungCap.ten_ncc).all())


@bp.route('/tong-hop')
@quyen_required('cong_no', 'xem')
def tong_hop():
    """Tong no tung khach hang so voi han muc cho phep."""
    rows = (db.session.query(CongNo.khach_hang_id, db.func.sum(CongNo.so_tien - CongNo.da_thanh_toan),
                             db.func.count(CongNo.id))
            .filter(CongNo.doi_tuong == 'khach_hang', CongNo.so_tien > CongNo.da_thanh_toan)
            .group_by(CongNo.khach_hang_id).all())
    ds = []
    for kh_id, tong, so_ct in rows:
        kh = db.session.get(KhachHang, kh_id)
        qua_han = sum(c.con_lai for c in kh.cong_nos if c.qua_han)
        ds.append({'kh': kh, 'tong': tong, 'so_ct': so_ct, 'han_muc': kh.han_muc_no_ap_dung, 'qua_han': qua_han,
                   'vuot': tong > kh.han_muc_no_ap_dung})
    ds.sort(key=lambda d: (not d['vuot'], -d['qua_han'], -d['tong']))
    rows_ncc = (db.session.query(CongNo.nha_cung_cap_id, db.func.sum(CongNo.so_tien - CongNo.da_thanh_toan),
                                 db.func.count(CongNo.id))
                .filter(CongNo.doi_tuong == 'nha_cung_cap', CongNo.so_tien > CongNo.da_thanh_toan)
                .group_by(CongNo.nha_cung_cap_id).all())
    ds_ncc = [{'ncc': db.session.get(NhaCungCap, i), 'tong': t, 'so_ct': n} for i, t, n in rows_ncc]
    return render_template('congno/tong_hop.html', ds=ds, ds_ncc=ds_ncc)


@bp.route('/<int:id>', methods=['GET', 'POST'])
@quyen_required('cong_no', 'xem')
def chi_tiet(id):
    cn = db.session.get(CongNo, id) or abort(404)
    if request.method == 'POST':
        if not current_user.co_quyen('cong_no', 'them'):
            abort(403)
        try:
            congno.thanh_toan(cn, so_thuc(request.form.get('so_tien')), request.form.get('hinh_thuc', 'tien_mat'),
                              current_user, request.form.get('ghi_chu') or None)
            db.session.commit()
            flash('Đã ghi nhận thanh toán công nợ.', 'success')
            return redirect(url_for('congno.chi_tiet', id=id))
        except LoiNghiepVu as e:
            db.session.rollback()
            flash(str(e), 'danger')
    return render_template('congno/chi_tiet.html', cn=cn,
                           hinh_thucs={k: v for k, v in HINH_THUC_TT.items() if k != 'ghi_no'})
