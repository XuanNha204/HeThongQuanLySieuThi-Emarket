import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'emarket-dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'emarket.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # file import Excel toi da 10MB

    # --- Quy tac nghiep vu ---
    NGUONG_THE_THAN_THIET = 100_000   # gia tri 1 lan mua de duoc lap the (VND)
    SO_TIEN_MOI_DIEM = 10_000         # moi 10.000d thanh toan = 1 diem
    GIA_TRI_MOT_DIEM = 100            # 1 diem quy doi = 100d khi thanh toan
    SO_NGAY_NO_MAC_DINH = 30          # han tra no mac dinh (ngay)
    HAN_MUC_NO_MAC_DINH = 5_000_000   # muc no toi da mac dinh cua 1 khach hang
    SO_NGAY_NO_NCC = 30               # han tra no nha cung cap mac dinh (ngay)

    # --- Tac vu tu dong ---
    SCHEDULER_ENABLED = True
    KIEM_TRA_CANH_BAO_PHUT = 5        # chu ky kiem tra ton kho / cong no (phut)
    BACKUP_GIO = 23                   # sao luu du lieu hang ngay luc 23:00
    BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
    BACKUP_GIU_LAI = 30               # so ban sao luu giu lai

    KIOSK_TU_RESET_GIAY = 90          # man hinh kiosk tu quay ve trang chu


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False
    SCHEDULER_ENABLED = False
