"""Ban hang: POS tai quay (quet ma vach), don hang online, hoa don, gia ban theo khach hang (SD01, SD02, SD09, SD11)."""
from datetime import datetime, time

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user

from app.extensions import db
from app.models import (HangHoa, KhachHang, Kho, DonHang, HoaDon, GiaBanTheoKH, TheThanhThiet, TRANG_THAI_DON,
                        LoaiHangHoa)
from app.services import LoiNghiepVu, banhang, excel
from app.utils.decorators import quyen_required
from app.utils.filters import vnd
from app.utils.helpers import so_thuc, so_nguyen, doc_ngay

bp = Blueprint('banhang', __name__)


# ---------------------------------------------------------------- POS tai quay
@bp.route('/pos')
@quyen_required('hoa_don', 'them')
def pos():
    khos = Kho.query.filter_by(trang_thai=True).order_by(Kho.ma_kho).all()
    return render_template('banhang/pos.html', khos=khos, loais=LoaiHangHoa.query.order_by(LoaiHangHoa.ten_loai).all())


def _hang_hoa_json(hh, kh, kho_id):
    gia, ghi_chu = banhang.ap_gia(hh, kh)
    return {'id': hh.id, 'ma': hh.ma_hang, 'ma_vach': hh.ma_vach, 'ten': hh.ten_hang, 'dvt': hh.don_vi_tinh,
            'loai': hh.loai_hang_id, 'gia': gia, 'gia_niem_yet': hh.gia_ban, 'ghi_chu_gia': ghi_chu,
            'ton': hh.ton_tai_kho(kho_id) if kho_id else hh.tong_ton}


@bp.route('/api/hang-hoa')
@quyen_required('hoa_don', 'xem')
def api_hang_hoa():
    kh = db.session.get(KhachHang, request.args.get('kh_id', type=int) or 0)
    kho_id = request.args.get('kho_id', type=int)
    q = HangHoa.query.filter_by(trang_thai=True)
    tu_khoa = request.args.get('q', '').strip()
    if tu_khoa:
        q = q.filter(db.or_(HangHoa.ma_vach == tu_khoa, HangHoa.ma_hang == tu_khoa,
                            HangHoa.ten_hang.ilike(f'%{tu_khoa}%')))
    return jsonify([_hang_hoa_json(hh, kh, kho_id) for hh in q.order_by(HangHoa.ten_hang).limit(500)])


@bp.route('/api/khach-hang')
@quyen_required('hoa_don', 'xem')
def api_khach_hang():
    tu_khoa = request.args.get('q', '').strip()
    if len(tu_khoa) < 2:
        return jsonify([])
    ds = (KhachHang.query.outerjoin(TheThanhThiet).filter(KhachHang.trang_thai.is_(True))
          .filter(db.or_(KhachHang.dien_thoai.ilike(f'%{tu_khoa}%'), KhachHang.ho_ten.ilike(f'%{tu_khoa}%'),
                         KhachHang.ma_kh == tu_khoa, TheThanhThiet.ma_the == tu_khoa))
          .limit(10).all())
    return jsonify([{'id': k.id, 'ma': k.ma_kh, 'ten': k.ho_ten, 'dien_thoai': k.dien_thoai,
                     'loai': k.loai_khach_hang.ten_loai if k.loai_khach_hang else '',
                     'the': k.the_than_thiet.ma_the if k.co_the else None, 'diem': k.diem_tich_luy or 0}
                    for k in ds])


@bp.route('/pos/thanh-toan', methods=['POST'])
@quyen_required('hoa_don', 'them')
def pos_thanh_toan():
    d = request.get_json(silent=True) or {}
    kh = db.session.get(KhachHang, int(d.get('kh_id') or 0)) if d.get('kh_id') else None
    try:
        hd = banhang.thanh_toan_tai_quay(current_user, kh, d.get('items') or [], so_nguyen(d.get('kho_id')),
                                         d.get('hinh_thuc_tt') or 'tien_mat', so_nguyen(d.get('diem_su_dung')),
                                         so_thuc(d.get('tien_khach_dua')))
        db.session.commit()
    except LoiNghiepVu as e:
        db.session.rollback()
        return jsonify(ok=False, loi=str(e)), 400
    don = hd.don_hang
    return jsonify(ok=True, ma_hd=hd.ma_hd, tong=hd.tong_tien, tien_thoi=max(0, hd.tien_khach_dua - hd.tong_tien),
                   diem_cong=don.diem_cong, co_the_moi=bool(kh and kh.the_than_thiet
                                                            and kh.the_than_thiet.chung_tu_dat_dieu_kien == hd.ma_hd),
                   url_in=url_for('banhang.in_hoa_don', id=hd.id))


# ---------------------------------------------------------------- hoa don
@bp.route('/hoa-don')
@quyen_required('hoa_don', 'xem')
def hoa_don():
    q = HoaDon.query.join(DonHang)
    tu, den = doc_ngay(request.args.get('tu')), doc_ngay(request.args.get('den'))
    if tu:
        q = q.filter(HoaDon.ngay_lap >= datetime.combine(tu, time.min))
    if den:
        q = q.filter(HoaDon.ngay_lap <= datetime.combine(den, time.max))
    if request.args.get('q'):
        q = q.outerjoin(KhachHang, DonHang.khach_hang_id == KhachHang.id).filter(
            db.or_(HoaDon.ma_hd.ilike(f"%{request.args['q']}%"), KhachHang.ho_ten.ilike(f"%{request.args['q']}%")))
    q = q.order_by(HoaDon.ngay_lap.desc())
    if request.args.get('xuat') and current_user.co_quyen('hoa_don', 'in_an'):
        return excel.xuat('hoa_don.xlsx', 'DANH SÁCH HÓA ĐƠN',
                          ['Mã HĐ', 'Ngày lập', 'Khách hàng', 'Nguồn', 'Tổng tiền', 'Hình thức TT', 'Nhân viên'],
                          [[h.ma_hd, h.ngay_lap, h.don_hang.khach_hang.ho_ten if h.don_hang.khach_hang else 'Khách lẻ',
                            'Online' if h.don_hang.nguon == 'online' else 'Tại quầy', h.tong_tien, h.ten_hinh_thuc,
                            h.nhan_vien.ho_ten if h.nhan_vien else ''] for h in q])
    trang = q.paginate(page=request.args.get('page', 1, type=int), per_page=25, error_out=False)
    return render_template('banhang/hoa_don.html', trang=trang)


@bp.route('/hoa-don/<int:id>/in')
@quyen_required('hoa_don', 'xem')
def in_hoa_don(id):
    hd = db.session.get(HoaDon, id) or abort(404)
    return render_template('banhang/hoa_don_in.html', hd=hd, don=hd.don_hang)


# ---------------------------------------------------------------- don hang
@bp.route('/don-hang')
@quyen_required('don_hang', 'xem')
def don_hang():
    q = DonHang.query
    tt = request.args.get('trang_thai')
    if tt in TRANG_THAI_DON:
        q = q.filter_by(trang_thai=tt)
    nguon = request.args.get('nguon', 'online')
    if nguon in ('online', 'tai_quay'):
        q = q.filter_by(nguon=nguon)
    if request.args.get('q'):
        q = q.outerjoin(KhachHang, DonHang.khach_hang_id == KhachHang.id).filter(
            db.or_(DonHang.ma_don.ilike(f"%{request.args['q']}%"), KhachHang.ho_ten.ilike(f"%{request.args['q']}%"),
                   KhachHang.dien_thoai.ilike(f"%{request.args['q']}%")))
    dem = dict(db.session.query(DonHang.trang_thai, db.func.count(DonHang.id))
               .filter(DonHang.nguon == 'online').group_by(DonHang.trang_thai).all())
    trang = q.order_by(DonHang.ngay_dat.desc()).paginate(page=request.args.get('page', 1, type=int),
                        per_page=25, error_out=False)
    return render_template('banhang/don_hang.html', trang=trang, dem=dem, nguon=nguon)


@bp.route('/don-hang/<int:id>')
@quyen_required('don_hang', 'xem')
def don_hang_chi_tiet(id):
    don = db.session.get(DonHang, id) or abort(404)
    return render_template('banhang/don_hang_chi_tiet.html', don=don)


@bp.route('/don-hang/<int:id>/trang-thai', methods=['POST'])
@quyen_required('don_hang', 'sua')
def cap_nhat_trang_thai(id):
    don = db.session.get(DonHang, id) or abort(404)
    moi = request.form.get('trang_thai')
    if moi == 'hoan_thanh' and not current_user.co_quyen('hoa_don', 'them'):
        abort(403)
    try:
        banhang.chuyen_trang_thai(don, moi, current_user, request.form.get('hinh_thuc_tt', 'tien_mat'),
                                  request.form.get('ghi_chu') or None)
        db.session.commit()
        flash(f'Đơn {don.ma_don} đã chuyển sang "{don.ten_trang_thai}".', 'success')
    except LoiNghiepVu as e:
        db.session.rollback()
        flash(str(e), 'danger')
    return redirect(url_for('banhang.don_hang_chi_tiet', id=id))


# ---------------------------------------------------------------- gia ban theo khach hang
@bp.route('/gia-ban', methods=['GET', 'POST'])
@quyen_required('gia_ban', 'xem')
def gia_ban():
    kh = db.session.get(KhachHang, request.args.get('kh_id', type=int) or 0)
    if request.method == 'POST':
        if not current_user.co_quyen('gia_ban', 'them'):
            abort(403)
        kh = db.session.get(KhachHang, request.form.get('kh_id', type=int) or 0)
        hh = db.session.get(HangHoa, request.form.get('hang_hoa_id', type=int) or 0)
        gia = so_thuc(request.form.get('gia_ban'), -1)
        if not kh or not hh:
            flash('Vui lòng chọn khách hàng và mặt hàng.', 'danger')
        elif gia <= 0:
            flash('Giá bán phải lớn hơn 0.', 'danger')
        else:
            gb = GiaBanTheoKH.query.filter_by(khach_hang_id=kh.id, hang_hoa_id=hh.id).first()
            if gb is None:
                gb = GiaBanTheoKH(khach_hang=kh, hang_hoa=hh)
                db.session.add(gb)
            gb.gia_ban, gb.ghi_chu, gb.ngay_ap_dung = gia, request.form.get('ghi_chu') or None, datetime.now()
            db.session.commit()
            flash(f'Đã áp giá {vnd(gia)} cho "{hh.ten_hang}" - {kh.ho_ten}.', 'success')
        return redirect(url_for('banhang.gia_ban', kh_id=kh.id if kh else None))
    q = GiaBanTheoKH.query
    if kh:
        q = q.filter_by(khach_hang_id=kh.id)
    ds = q.order_by(GiaBanTheoKH.ngay_ap_dung.desc()).all()
    return render_template('banhang/gia_ban.html', ds=ds, kh=kh,
                           khach_hangs=KhachHang.query.filter_by(trang_thai=True).order_by(KhachHang.ho_ten).all(),
                           hang_hoas=HangHoa.query.filter_by(trang_thai=True).order_by(HangHoa.ten_hang).all())


@bp.route('/gia-ban/<int:id>/xoa', methods=['POST'])
@quyen_required('gia_ban', 'xoa')
def xoa_gia_ban(id):
    gb = db.session.get(GiaBanTheoKH, id) or abort(404)
    kh_id = gb.khach_hang_id
    db.session.delete(gb)
    db.session.commit()
    flash('Đã xóa giá riêng, khách hàng sẽ áp giá theo loại KH / giá niêm yết.', 'info')
    return redirect(url_for('banhang.gia_ban', kh_id=kh_id))
