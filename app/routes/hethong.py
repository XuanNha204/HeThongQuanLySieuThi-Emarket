"""He thong: nguoi dung & phan quyen chi tiet (SD15), canh bao, sao luu hang ngay."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file, current_app
from flask_login import current_user

from app.extensions import db
from app.models import NguoiDung, PhanQuyen, ThongBao, CHUC_NANG, QUYEN, VAI_TRO, LOAI_THONG_BAO
from app.models.nguoidung import QUYEN_MAC_DINH
from app.services import thongbao, backup
from app.utils.decorators import quyen_required, nhan_vien_required

bp = Blueprint('hethong', __name__)


# ---------------------------------------------------------------- nguoi dung & phan quyen
@bp.route('/nguoi-dung')
@quyen_required('he_thong', 'xem')
def nguoi_dung():
    return render_template('hethong/nguoi_dung.html', ds=NguoiDung.query.order_by(NguoiDung.id).all())


def _luu_phan_quyen(nd, form):
    hien_co = {pq.chuc_nang: pq for pq in nd.phan_quyens}
    for cn in CHUC_NANG:
        pq = hien_co.get(cn)
        if pq is None:
            pq = PhanQuyen(chuc_nang=cn)
            nd.phan_quyens.append(pq)
        for q in QUYEN:
            setattr(pq, q, bool(form.get(f'q_{cn}_{q}')))
        if any(getattr(pq, q) for q in QUYEN if q != 'xem'):
            pq.xem = True  # co quyen thao tac thi phai xem duoc


@bp.route('/nguoi-dung/them', methods=['GET', 'POST'])
@bp.route('/nguoi-dung/<int:id>/sua', methods=['GET', 'POST'])
@quyen_required('he_thong', 'sua')
def nguoi_dung_form(id=None):
    nd = db.session.get(NguoiDung, id) if id else NguoiDung(vai_tro='ban_hang', trang_thai=True)
    if nd is None:
        abort(404)
    if request.method == 'POST':
        f = request.form
        loi = []
        username = f.get('username', '').strip()
        if not username or not f.get('ho_ten', '').strip():
            loi.append('Vui lòng nhập tên đăng nhập và họ tên.')
        elif NguoiDung.query.filter(NguoiDung.username == username, NguoiDung.id != (nd.id or 0)).first():
            loi.append(f'Tên đăng nhập "{username}" đã tồn tại.')
        if f.get('vai_tro') not in VAI_TRO:
            loi.append('Vai trò không hợp lệ.')
        mk = f.get('password', '')
        if (not nd.id and len(mk) < 6) or (mk and len(mk) < 6):
            loi.append('Mật khẩu tối thiểu 6 ký tự.')
        if nd.id == current_user.id and (f.get('vai_tro') != 'admin' and nd.is_admin or not f.get('trang_thai')):
            loi.append('Không thể tự hạ quyền quản trị hoặc tự khóa tài khoản đang đăng nhập.')
        if loi:
            for e in loi:
                flash(e, 'danger')
        else:
            nd.username, nd.ho_ten = username, f['ho_ten'].strip()
            nd.email, nd.dien_thoai = f.get('email') or None, f.get('dien_thoai') or None
            nd.vai_tro, nd.trang_thai = f['vai_tro'], bool(f.get('trang_thai'))
            if mk:
                nd.set_password(mk)
            if not nd.id:
                db.session.add(nd)
            _luu_phan_quyen(nd, f)
            db.session.commit()
            flash(f'Đã lưu người dùng {nd.username} và phân quyền.', 'success')
            return redirect(url_for('hethong.nguoi_dung'))
    quyen_hien_tai = {pq.chuc_nang: {q for q in QUYEN if getattr(pq, q)} for pq in nd.phan_quyens}
    if not nd.id:
        quyen_hien_tai = QUYEN_MAC_DINH.get(nd.vai_tro, {})
    mac_dinh = {vt: {cn: sorted(qs) for cn, qs in QUYEN_MAC_DINH.get(vt, {}).items()} for vt in VAI_TRO}
    return render_template('hethong/nguoi_dung_form.html', nd=nd, quyen=quyen_hien_tai, mac_dinh=mac_dinh)


# ---------------------------------------------------------------- canh bao
@bp.route('/thong-bao')
@nhan_vien_required
def thong_bao():
    xem = request.args.get('xem', 'hieu_luc')
    q = ThongBao.query.filter_by(da_xu_ly=(xem == 'da_xu_ly'))
    loai = request.args.get('loai')
    if loai:
        q = q.filter_by(loai=loai)
    ds = q.order_by(ThongBao.ngay_tao.desc()).limit(300).all()
    return render_template('hethong/thong_bao.html', ds=ds, xem=xem, loai=loai, loais=LOAI_THONG_BAO)


@bp.route('/thong-bao/kiem-tra', methods=['POST'])
@nhan_vien_required
def kiem_tra_thong_bao():
    so_moi = thongbao.kiem_tra_tat_ca()
    db.session.commit()
    flash(f'Đã kiểm tra tồn kho và công nợ: {so_moi} cảnh báo mới.', 'info')
    return redirect(url_for('hethong.thong_bao'))


@bp.route('/thong-bao/da-doc', methods=['POST'])
@nhan_vien_required
def danh_dau_da_doc():
    ThongBao.query.filter_by(da_xu_ly=False, da_doc=False).update({'da_doc': True})
    db.session.commit()
    return redirect(url_for('hethong.thong_bao'))


@bp.route('/thong-bao/<int:id>/mo')
@nhan_vien_required
def mo_thong_bao(id):
    tb = db.session.get(ThongBao, id) or abort(404)
    tb.da_doc = True
    db.session.commit()
    return redirect(tb.lien_ket or url_for('hethong.thong_bao'))


# ---------------------------------------------------------------- sao luu
@bp.route('/sao-luu', methods=['GET', 'POST'])
@quyen_required('he_thong', 'xem')
def sao_luu():
    if request.method == 'POST':
        if not current_user.co_quyen('he_thong', 'them'):
            abort(403)
        try:
            flash(f'Đã sao lưu dữ liệu: {backup.sao_luu()}', 'success')
        except (RuntimeError, OSError) as e:
            flash(f'Sao lưu thất bại: {e}', 'danger')
        return redirect(url_for('hethong.sao_luu'))
    return render_template('hethong/sao_luu.html', ds=backup.danh_sach(), gio=current_app.config['BACKUP_GIO'],
                           giu_lai=current_app.config['BACKUP_GIU_LAI'])


@bp.route('/sao-luu/<ten>')
@quyen_required('he_thong', 'in_an')
def tai_sao_luu(ten):
    p = backup.duong_dan(ten) or abort(404)
    return send_file(p, as_attachment=True, download_name=ten)


# ---------------------------------------------------------------- tai khoan ca nhan
@bp.route('/doi-mat-khau', methods=['GET', 'POST'])
@nhan_vien_required
def doi_mat_khau():
    if request.method == 'POST':
        if not current_user.check_password(request.form.get('cu', '')):
            flash('Mật khẩu hiện tại không đúng.', 'danger')
        elif len(request.form.get('moi', '')) < 6 or request.form.get('moi') != request.form.get('nhap_lai'):
            flash('Mật khẩu mới tối thiểu 6 ký tự và phải nhập lại trùng khớp.', 'danger')
        else:
            current_user.set_password(request.form['moi'])
            db.session.commit()
            flash('Đã đổi mật khẩu.', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('hethong/doi_mat_khau.html')
