from datetime import datetime

from app.extensions import db


def sinh_ma(prefix, cot):
    """Sinh ma chung tu tang dan theo ngay: <prefix><yymmdd><0001>."""
    goc = f"{prefix}{datetime.now():%y%m%d}"
    lon_nhat = db.session.query(db.func.max(cot)).filter(cot.like(goc + '%')).scalar()
    so = int(lon_nhat[len(goc):]) + 1 if lon_nhat and lon_nhat[len(goc):].isdigit() else 1
    return f"{goc}{so:04d}"


def so_thuc(v, mac_dinh=0.0):
    try:
        return float(str(v).replace(',', '').strip()) if v not in (None, '') else mac_dinh
    except ValueError:
        return mac_dinh


def so_nguyen(v, mac_dinh=0):
    return int(so_thuc(v, mac_dinh))


def doc_ngay(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v.date()
    if hasattr(v, 'year'):
        return v
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(str(v).strip(), fmt).date()
        except ValueError:
            continue
    return None
