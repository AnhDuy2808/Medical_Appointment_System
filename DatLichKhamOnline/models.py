import hashlib
import uuid
from datetime import datetime, time, timedelta, date
from enum import Enum as PyEnum
from typing import List
import csv

from flask_login import UserMixin
from sqlalchemy import String, Date, Time, ForeignKey
from sqlalchemy.orm import relationship

from DatLichKhamOnline import app, db


# Bỏ lớp Base không còn cần thiết
# class Base(db.DeclarativeBase):
#     pass

class UserRole(PyEnum):
    ADMIN = "admin"
    USER = "user"
    DOCTOR = "doctor"


class TicketStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    birth_of_day = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    doctor = relationship("Doctor", back_populates="user", uselist=False)
    tickets = relationship("Ticket", back_populates="client")

    def __str__(self): return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @staticmethod
    def hash_password(password): return hashlib.md5(password.encode('utf-8')).hexdigest()

    def check_password(self, password): return self.password == self.hash_password(password)


class MedicalCenter(db.Model):
    __tablename__ = 'medical_centers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    image = db.Column(db.Text, nullable=True)
    doctors = relationship("Doctor", back_populates="medical_center")

    def __str__(self): return self.name


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    doctor_departments = relationship("DoctorDepartment", back_populates="department")

    def __str__(self): return self.name


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    medical_center_id = db.Column(db.Integer, db.ForeignKey('medical_centers.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    start_year = db.Column(db.Integer, nullable=True)
    user = relationship("User", back_populates="doctor")
    medical_center = relationship("MedicalCenter", back_populates="doctors")
    doctor_departments = relationship("DoctorDepartment", back_populates="doctor")
    doctor_shifts = relationship("DoctorShift", back_populates="doctor")


class DoctorDepartment(db.Model):
    __tablename__ = 'doctor_departments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    doctor = relationship("Doctor", back_populates="doctor_departments")
    department = relationship("Department", back_populates="doctor_departments")


class Shift(db.Model):
    __tablename__ = 'shifts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    doctor_shifts = relationship("DoctorShift", back_populates="shift")


class DoctorShift(db.Model):
    __tablename__ = 'doctor_shifts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False)
    work_date = db.Column(db.Date, nullable=False)
    doctor = relationship("Doctor", back_populates="doctor_shifts")
    shift = relationship("Shift", back_populates="doctor_shifts")
    ticket = relationship("Ticket", back_populates="doctor_shift", uselist=False)


class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    uuid = db.Column(db.String(255), unique=True, default=lambda: str(uuid.uuid4()))
    doctor_shift_id = db.Column(db.Integer, db.ForeignKey('doctor_shifts.id'), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum(TicketStatus), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    birth_of_day = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    doctor_shift = relationship("DoctorShift", back_populates="ticket")
    client = relationship("User", back_populates="tickets")


if __name__ == '__main__':
    with app.app_context():
        print("Đang xóa và tạo lại các bảng...")
        db.drop_all()
        db.create_all()
        print("Hoàn tất!")

        print("\n--- Đang tạo dữ liệu mẫu ---")

        # ... (Phần code tạo dữ liệu mẫu giữ nguyên như trước)
        print("-> Đang tạo trung tâm y tế và khoa...")
        medical_centers_data = [
            {'name': 'Bệnh viện Tâm Trí Sài Gòn',
             'address': '171 Trường Chinh, P. Tân Thới Nhất, Q. 12, TP. HCM',
             'phone': '02862601100',
             'image': 'https://lh3.googleusercontent.com/p/AF1QipPzH9SRDkbE887um6U72t89F9jNW5T5S_T8rwoo=s1360-w1360-h1020-rw',
             'description': 'Bệnh viện đa khoa tư nhân, cung cấp dịch vụ khám chữa bệnh tổng quát và chuyên khoa, nổi bật với dịch vụ chăm sóc khách hàng.'},

            {'name': 'Bệnh viện Mắt TP.Hồ Chí Minh',
             'address': '280 Điện Biên Phủ, P. Võ Thị Sáu, Q. 3, TP. HCM',
             'phone': '02839325364',
             'image': 'https://cdn.nhathuoclongchau.com.vn/unsafe/https://cms-prod.s3-sgn09.fptcloud.com/gioi_thieu_tong_quan_ve_benh_vien_mat_thanh_pho_ho_chi_minh_1_4776e2e07c.png',
             'description': 'Bệnh viện chuyên khoa mắt tuyến cuối, chuyên sâu về phẫu thuật mắt, điều trị tật khúc xạ và các bệnh lý nhãn khoa.'},

            {'name': 'Bệnh viện Đại học Y Dược TP.Hồ Chí Minh',
             'address': '215 Hồng Bàng, P. 11, Q. 5, TP. HCM',
             'phone': '02838554260',
             'image': 'https://giuongbenh.com/wp-content/uploads/2023/10/benh-vien-dai-hoc-y-duoc.jpg',
             'description': 'Bệnh viện đa khoa hạng đặc biệt, kết hợp đào tạo - nghiên cứu - điều trị, nổi bật ở các chuyên khoa tim mạch, gan mật và ngoại khoa phức tạp.'},

            {'name': 'Bệnh viện Đa khoa Vạn Hạnh',
             'address': '781/B1-B3-B5 Lê Hồng Phong, P. 12, Q. 10, TP. HCM',
             'phone': '02838632553',
             'image': 'https://benhvienvanhanh.vn/wp-content/uploads/2020/03/hinh.jpg',
             'description': 'Bệnh viện tư nhân đa khoa, mạnh về tim mạch, tiêu hóa, chấn thương chỉnh hình và dịch vụ chăm sóc khách hàng.'},

            {'name': 'Bệnh viện Quân Y 175',
             'address': '786 Nguyễn Kiệm, P. 3, Q. Gò Vấp, TP. HCM',
             'phone': '19001175',
             'image': 'https://data-service.pharmacity.io/pmc-upload-media/production/pmc-ecm-asm/blog/benh-vien-quan-y-115.webp',
             'description': 'Bệnh viện tuyến cuối của quân đội, chuyên sâu về chấn thương chỉnh hình, cấp cứu và hồi sức, có trung tâm điều trị quốc tế.'},

            {'name': 'Bệnh viện Răng - Hàm - Mặt TP.Hồ Chí Minh',
             'address': '263-265 Trần Hưng Đạo, P. Cô Giang, Q. 1, TP. HCM',
             'phone': '02838360191',
             'image': 'https://bvranghammat.com/wp-content/uploads/2020/04/654erdfs-1.jpg',
             'description': 'Bệnh viện chuyên khoa Răng - Hàm - Mặt hàng đầu, nổi bật với nha khoa thẩm mỹ, phẫu thuật hàm mặt và cấy ghép implant.'},

            {'name': 'Bệnh viện Chợ Rẫy',
             'address': '201B Nguyễn Chí Thanh, P. 12, Q. 5, TP. HCM',
             'phone': '02838554137',
             'image': 'https://phunuvietnam.mediacdn.vn/thumb_w/700/179072216278405120/2025/6/21/bvcrrr-17505074315051891270548-149-0-1749-2560-crop-1750507440184923419044.jpg',
             'description': 'Bệnh viện đa khoa tuyến cuối lớn nhất phía Nam, nổi tiếng về cấp cứu, hồi sức, tim mạch, ung bướu và ghép tạng.'},

            {'name': 'Bệnh viện Tân Bình',
             'address': '605 Hoàng Văn Thụ, P. 4, Q. Tân Bình, TP. HCM',
             'phone': '02838449928',
             'image': 'https://bvtb.org.vn/wp-content/uploads/2022/04/hinh_nen_1-2-e1650441246965.jpg',
             'description': 'Bệnh viện đa khoa tuyến quận, phục vụ chăm sóc sức khỏe tổng quát cho người dân quận Tân Bình và khu vực lân cận.'},

            {'name': 'Bệnh viện Tâm thần TP.Hồ Chí Minh',
             'address': '766 Võ Văn Kiệt, P. 1, Q. 5, TP. HCM',
             'phone': '02839234675',
             'image': 'https://bvtt-tphcm.org.vn/wp-content/uploads/2017/08/BVTT.jpg',
             'description': 'Bệnh viện chuyên khoa tâm thần tuyến cuối, chuyên điều trị các rối loạn tâm thần, tâm lý và nghiện chất.'},

            {'name': 'Bệnh viện Nguyễn Tri Phương',
             'address': '468 Nguyễn Trãi, P. 8, Q. 5, TP. HCM',
             'phone': '02839234332',
             'image': 'https://vivita.vn/wp-content/uploads/2021/07/bv-nguyen-tri-phuong-cong-chinh.jpg',
             'description': 'Bệnh viện đa khoa hạng I, thế mạnh ở các chuyên khoa nội tiết, tim mạch, ngoại tiêu hóa và cấp cứu.'},

            {'name': 'Bệnh viện Đa khoa Tâm Anh TP.Hồ Chí Minh',
             'address': '2B Phổ Quang, P. 2, Q. Tân Bình, TP. HCM',
             'phone': '02871026789',
             'image': 'https://ecopharma.com.vn/wp-content/uploads/2024/05/benh-vien-tam-anh.jpg',
             'description': 'Bệnh viện tư nhân cao cấp, nổi bật với sản phụ khoa, hiếm muộn - IVF, tim mạch và nhi khoa.'},

            {'name': 'Bệnh viện Từ Dũ',
             'address': '284 Cống Quỳnh, P. Phạm Ngũ Lão, Q. 1, TP. HCM',
             'phone': '02854042829',
             'image': 'https://prod-cdn.pharmacity.io/blog/benh-vien-tu-du-la-benh-vien-chuyen-khoa-phu-san-hiem-muon-hang-dau-phia-nam.jpeg',
             'description': 'Bệnh viện chuyên khoa phụ sản lớn nhất phía Nam, nổi tiếng về sản khoa, hiếm muộn, hỗ trợ sinh sản và chăm sóc trẻ sơ sinh.'},

            {'name': 'Bệnh viện Nhân Dân 115',
             'address': '527 Sư Vạn Hạnh, P. 12, Q. 10, TP. HCM',
             'phone': '02838652368',
             'image': 'https://dbnd.1cdn.vn/2025/06/08/q.jpg',
             'description': 'Bệnh viện đa khoa hạng I, thế mạnh về tim mạch can thiệp, thần kinh, đột quỵ và hồi sức cấp cứu.'},

            {'name': 'Bệnh viện FV',
             'address': '6 Nguyễn Lương Bằng, P. Tân Phú, Q. 7, TP. HCM',
             'phone': '02854113333',
             'image': 'https://aihealth.vn/app/uploads/2020/07/benh-vien-FV-2.jpg',
             'description': 'Bệnh viện quốc tế theo tiêu chuẩn JCI, cung cấp dịch vụ đa khoa, nổi bật về ung bướu, ngoại khoa và chăm sóc chất lượng cao.'},

            {'name': 'Bệnh viện Nhi Đồng 1',
             'address': '341 Sư Vạn Hạnh, P. 10, Q. 10, TP. HCM',
             'phone': '02839271119',
             'image': 'https://nhidong.org.vn/UploadImages/bvnhidong/PHP06/2023_5/bvdna.jpg',
             'description': 'Bệnh viện nhi khoa tuyến cuối, chuyên điều trị các bệnh lý trẻ em, phẫu thuật nhi và sơ sinh.'},

            {'name': 'Bệnh viện Tai - Mũi - Họng TP.Hồ Chí Minh',
             'address': '153 - 155 - 157 Trần Quốc Thảo, Phường 9, Quận 3, Hồ Chí Minh',
             'phone': '02839317381',
             'image': 'https://cdn.nhathuoclongchau.com.vn/unsafe/https://cms-prod.s3-sgn09.fptcloud.com/benh_vien_tai_mui_hong_thanh_pho_ho_chi_minh_thong_tin_tong_quat_can_biet_15c70b4d2b.jpg',
             'description': 'Bệnh viện chuyên khoa Tai - Mũi - Họng hàng đầu, mạnh về phẫu thuật tai, thanh quản, điều trị bệnh lý mũi xoang và họng.'},

            {'name': 'Bệnh viện Nhân Dân Gia Định',
             'address': '1 Nơ Trang Long, P. 7, Q. Bình Thạnh, TP. HCM',
             'phone': '02838412692',
             'image': 'https://cdn.benhvienquan11.vn/editor/2023/Benh%20vien%20nhan%20dan%20gia%20dinh/bvgd-1_25220238.jpg',
             'description': 'Bệnh viện đa khoa hạng I, mạnh về tim mạch, ngoại khoa và hồi sức cấp cứu.'},

            {'name': 'Bệnh viện Bình Dân',
             'address': '371 Điện Biên Phủ, P. 4, Q. 3, TP. HCM',
             'phone': '02838394747',
             'image': 'https://bvbinhdan.com.vn/vnt_upload/weblink/MAT_TIEN_TSC_BENH_VIEN_BINH_DAN_1440x510.png',
             'description': 'Chuyên khoa ngoại tổng quát, đặc biệt nổi tiếng với tiết niệu và nam khoa.'},

            {'name': 'Bệnh viện Trưng Vương',
             'address': '266 Lý Thường Kiệt, P. 14, Q. 10, TP. HCM',
             'phone': '02838653256',
             'image': 'https://tvh-api.medpro.com.vn/uploads/small_banner_trung_vuong_3510cc32e3.jpg?148205.33500000602',
             'description': 'Bệnh viện đa khoa hạng I, thế mạnh về cấp cứu, chấn thương và ngoại khoa.'},

            {'name': 'Bệnh viện Thống Nhất',
             'address': '1 Lý Thường Kiệt, P. 7, Q. 11, TP. HCM',
             'phone': '02838693731',
             'image': 'https://bvtn.org.vn/wp-content/uploads/2023/12/benh-vien-thong-nhat.jpg',
             'description': 'Bệnh viện đa khoa trung ương, nổi bật về tim mạch, lão khoa và ngoại khoa.'},

            {'name': 'Bệnh viện Hùng Vương',
             'address': '128 Hồng Bàng, P. 12, Q. 5, TP. HCM',
             'phone': '02838554137',
             'image': 'https://baonhien.vn/wp-content/uploads/hv2_1901162924.jpg',
             'description': 'Bệnh viện chuyên khoa sản phụ khoa lâu đời, nổi bật về chăm sóc thai kỳ và sản khoa.'},

            {'name': 'Bệnh viện Nhi Đồng 2',
             'address': '14 Lý Tự Trọng, P. Bến Nghé, Q. 1, TP. HCM',
             'phone': '02838295723',
             'image': 'https://data-service.pharmacity.io/pmc-upload-media/production/pmc-ecm-asm/blog/benh-vien-nhi-dong-2.webp',
             'description': 'Bệnh viện nhi tuyến cuối, nổi bật về phẫu thuật nhi, tim bẩm sinh và sơ sinh học.'},

            {'name': 'Bệnh viện Phạm Ngọc Thạch',
             'address': '120 Hồng Bàng, P. 12, Q. 5, TP. HCM',
             'phone': '02838554129',
             'image': 'https://prod-cdn.pharmacity.io/blog/benh-vien-pham-ngoc-thach.png?X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUYXZVMJMURHIYJSN%2F20240829%2Fap-southeast-1%2Fs3%2Faws4_request&X-Amz-Date=20240829T083734Z&X-Amz-SignedHeaders=host&X-Amz-Expires=600&X-Amz-Signature=748d2ba25c835f3eaa09d0178aaf47041da240e788319446295fdb92065d89d7',
             'description': 'Bệnh viện chuyên khoa hô hấp hàng đầu, nổi tiếng về điều trị lao và bệnh phổi.'},

            {'name': 'Bệnh viện An Sinh',
             'address': '10 Trần Huy Liệu, P. 12, Q. Phú Nhuận, TP. HCM',
             'phone': '02838457777',
             'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT4WlsO7D8bnbS_qRzqOLQurfPkqFPaOA_OgQ&s',
             'description': 'Bệnh viện tư nhân cao cấp, nổi bật với sản phụ khoa, nhi và tim mạch.'},

            {'name': 'Bệnh viện Quốc tế City',
             'address': 'Số 3 Đường 17A, P. Bình Trị Đông B, Q. Bình Tân, TP. HCM',
             'phone': '02862801168',
             'image': 'https://aihealth.vn/app/uploads/2020/07/benh-vien-quoc-te-city-1-1.jpg',
             'description': 'Bệnh viện quốc tế đa khoa, đạt tiêu chuẩn Singapore, mạnh về ngoại khoa và sản khoa.'},

            {'name': 'Bệnh viện Hoàn Mỹ Sài Gòn',
             'address': '60-60A Phan Xích Long, P. 1, Q. Phú Nhuận, TP. HCM',
             'phone': '02839908857',
             'image': 'https://insmart.com.vn/wp-content/uploads/2021/07/benh-vien-hoan-my-sai-gon.jpg',
             'description': 'Bệnh viện tư nhân đa khoa, mạnh về tim mạch, nội tiết, chấn thương chỉnh hình.'}
        ]

        for center_data in medical_centers_data:
            db.session.add(MedicalCenter(**center_data))

        db.session.commit()
        print(f"  + Đã tạo thành công {len(medical_centers_data)} trung tâm y tế.")

        department_names = [
            "Nhãn khoa", "Răng - Hàm - Mặt", "Tai - Mũi - Họng", "Tâm thần",
            "Da liễu", "Tiêu hóa - Gan mật", "Sản phụ khoa", "Tim mạch", "Hô hấp",
            "Chấn thương Chỉnh hình", "Ngoại tổng quát", "Nhi khoa", "Ung bướu"
        ]
        unique_departments = set(department_names)
        for name in unique_departments:
            db.session.add(Department(name=name))
        db.session.commit()
        print(f"  + Đã tạo thành công {len(unique_departments)} chuyên khoa.")
        print("-> Đang tạo người dùng mẫu...")
        admin_user = User(username='admin', password=User.hash_password('123'), email='admin@example.com',
                          role=UserRole.ADMIN, first_name='Admin', last_name='System')
        client_user = User(username='client1', password=User.hash_password('123'), email='client1@example.com',
                           role=UserRole.USER, first_name='Khách', last_name='Hàng A')
        db.session.add_all([admin_user, client_user])
        db.session.commit()
        print("-> Đang tạo các ca làm việc...")
        shifts = []
        for hour in range(7, 23):
            shifts.append(Shift(start_time=time(hour, 0), end_time=time(hour, 30)))
            shifts.append(Shift(start_time=time(hour, 30), end_time=time(hour + 1, 0)))
        db.session.add_all(shifts)
        db.session.commit()
        print("-> Bắt đầu thêm bác sĩ từ file DoctorInfo.csv...")
        try:
            medical_centers = db.session.query(MedicalCenter).all()
            departments = db.session.query(Department).all()
            center_lookup = {center.name.strip().lower(): center.id for center in medical_centers}
            department_lookup = {department.name.strip().lower(): department.id for department in departments}
            with open('data/DoctorInfo.csv', mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                print(reader.fieldnames)
                for row in reader:
                    existing_user = db.session.query(User).filter(
                        (User.username == row['username']) | (User.email == row['email'])
                    ).first()
                    if existing_user:
                        print(f"  - Bỏ qua, người dùng đã tồn tại: {row['username']}")
                        continue
                    new_user = User(
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        email=row['email'],
                        username=row['username'],
                        password=User.hash_password(row['password']),
                        role=UserRole.DOCTOR,
                        avatar=row['avatar']
                    )

                    db.session.add(new_user)
                    db.session.flush()
                    mc_name = row['medical_center_name'].strip().lower()
                    mc_id = center_lookup.get(mc_name)
                    dpm_name = row['department_name'].strip().lower()
                    dpm_id = department_lookup.get(dpm_name)
                    if not mc_id:
                        print(
                            f"  - Cảnh báo: Không tìm thấy trung tâm y tế '{row.get('medical_center_name')}' cho bác sĩ {row['username']}.")
                    if not dpm_id:
                        print(
                            f"- Cảnh báo: Không tìm thấy chuyên khoa '{row.get('deparment_name')}' cho bác sĩ {row['username']}."
                        )
                    new_doctor = Doctor(
                        id=new_user.id,
                        description=row.get('Introduce', ''),
                        start_year=int(row['start_year']) if row.get('start_year') else None,
                        medical_center_id=mc_id
                    )
                    db.session.add(new_doctor)
                    print(f"  + Đã thêm bác sĩ: {new_user.username}")

                    new_doctor_department = DoctorDepartment(
                        doctor_id=new_user.id,
                        department_id= dpm_id
                    )
                    db.session.add(new_doctor_department)
                    print(f" + Đã thêm chuyên khoa cho bác sĩ {new_user.username}")

            db.session.commit()
            print("-> Thêm bác sĩ từ CSV thành công!")
        except FileNotFoundError:
            print("-> Cảnh báo: Không tìm thấy file 'DoctorInfo.csv'. Bỏ qua bước thêm bác sĩ từ CSV.")
        except Exception as e:
            print(f"!!! Lỗi khi đọc file CSV: {e}")
            db.session.rollback()
        print("\n--- Hoàn thành tạo dữ liệu mẫu ---")