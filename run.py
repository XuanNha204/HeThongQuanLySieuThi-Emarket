"""Chay eMarket o moi truong dev: python run.py  (tu tao du lieu mau lan dau)."""
import os

os.environ.setdefault('FLASK_DEBUG', '1')

from app import create_app  # noqa: E402
from app.models import NguoiDung  # noqa: E402

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        can_seed = NguoiDung.query.first() is None
    # chi seed o tien trinh chinh (reloader cua Flask chay lai file nay trong tien trinh con)
    if can_seed and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        import seed
        print('CSDL trong - dang tao du lieu mau (mat khoang 1 phut)...')
        seed.tao_du_lieu(app)
    app.run(debug=True, host='127.0.0.1', port=5000)
