# DatLichKhamOnline/models.py

from sqlalchemy import Column, Integer, String, DateTime, Date, Time, ForeignKey
from sqlalchemy.orm import relationship, backref
from datetime import datetime, time, timedelta, date
from enum import Enum as UserEnum
from DatLichKhamOnline import app, db
import hashlib


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class UserRole(UserEnum):
    ADMIN = "admin"
    USER = "user"
    DOCTOR = "doctor"


# Định nghĩa lớp Ticket trước User vì User cần tham chiếu đến Ticket.client_id
class Ticket(BaseModel):
    __tablename__ = 'tickets'
    uuid = Column(String(255), unique=True, nullable=False)
    shifts_id = Column(Integer, ForeignKey('shifts.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(50), nullable=False)  # e.g., 'pending', 'confirmed', 'cancelled', 'completed'
    first_name = Column(String(255))
    last_name = Column(String(255))
    birth_of_day = Column(Date)
    gender = Column(String(50))
    appointment_time = Column(Time)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Quan hệ sẽ được thiết lập sau khi các lớp User và Shift được định nghĩa
    # client = relationship("User", back_populates="tickets_as_client")
    # shifts = relationship("Shift", back_populates="tickets")


class User(BaseModel):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128))
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Thêm các trường này
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    birth_of_day = db.Column(db.Date)
    gender = db.Column(db.String(10))  # Male, Female, Other
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    avatar = db.Column(db.String(255))
    doctor_departments = relationship("DoctorDepartment", back_populates="user")
    doctor_medical_centers = relationship("DoctorMedicalCenter", back_populates="user")
    shifts = relationship("Shift", back_populates="doctor")
    # Bây giờ Ticket đã được định nghĩa, nên có thể tham chiếu
    tickets_as_client = relationship("Ticket", back_populates="client", foreign_keys=[Ticket.client_id])

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @staticmethod
    def hash_password(password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    def check_password(self, password):
        return self.password == self.hash_password(password)


class MedicalCenter(BaseModel):
    __tablename__ = 'medical_centers'
    name = Column(String(255), nullable=False)
    address = Column(String(255))
    phone = Column(String(20))
    description = Column(String(255))
    image = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor_medical_centers = relationship("DoctorMedicalCenter", back_populates="medical_center")
    shifts = relationship("Shift", back_populates="medical_center")

    def __str__(self):
        return self.name


class Department(BaseModel):
    __tablename__ = 'departments'
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor_departments = relationship("DoctorDepartment", back_populates="department")

    def __str__(self):
        return self.name


class DoctorDepartment(BaseModel):
    __tablename__ = 'doctor_departments'
    doctor_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'), primary_key=True)
    description = Column(String(255))

    user = relationship("User", back_populates="doctor_departments")
    department = relationship("Department", back_populates="doctor_departments")


class DoctorMedicalCenter(BaseModel):
    __tablename__ = 'doctor_medical_centers'
    doctor_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    medical_center_id = Column(Integer, ForeignKey('medical_centers.id'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="doctor_medical_centers")
    medical_center = relationship("MedicalCenter", back_populates="doctor_medical_centers")


class Shift(BaseModel):
    __tablename__ = 'shifts'
    doctor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    medical_center_id = Column(Integer, ForeignKey('medical_centers.id'), nullable=False)
    work_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    max_patients = Column(Integer, default=0)
    current_patients = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor = relationship("User", back_populates="shifts")
    medical_center = relationship("MedicalCenter", back_populates="shifts")
    tickets = relationship("Ticket", back_populates="shifts", lazy=True)


# Sau khi tất cả các lớp liên quan đã được định nghĩa, thiết lập mối quan hệ còn thiếu cho Ticket
Ticket.client = relationship("User", back_populates="tickets_as_client")
Ticket.shifts = relationship("Shift", back_populates="tickets")

if __name__ == '__main__':
    with app.app_context():
        print("Đang xóa và tạo lại các bảng...")
        db.drop_all()
        db.create_all()
        print("Hoàn tất!")

        print("\n--- Đang tạo dữ liệu mẫu ---")

        # Tạo người dùng mẫu: băm mật khẩu bằng MD5
        admin_user = User(username='admin', password=User.hash_password('123'), email='admin@example.com',
                          role=UserRole.ADMIN.value, first_name='Admin', last_name='System')
        doctor1 = User(username='doc1', password=User.hash_password('123'), email='doctor1@example.com',
                       role=UserRole.DOCTOR.value, first_name='Lâm Việt', last_name='Trung')
        doctor2 = User(username='doc2', password=User.hash_password('123'), email='doctor2@example.com',
                       role=UserRole.DOCTOR.value, first_name='Phạm Thị', last_name='Mai')
        doctor3 = User(username='doc3', password=User.hash_password('123'), email='doctor3@example.com',
                       role=UserRole.DOCTOR.value, first_name='Lê Văn', last_name='Dũng')
        doctor4 = User(username='doc4', password=User.hash_password('123'), email='doctor4@example.com',
                       role=UserRole.DOCTOR.value, first_name='Trần Thị', last_name='Hương')
        client1 = User(username='client1', password=User.hash_password('123'), email='client1@example.com',
                       role=UserRole.USER.value, first_name='Khách', last_name='Hàng A')

        db.session.add_all([admin_user, doctor1, doctor2, doctor3, doctor4, client1])
        db.session.commit()
        print("Đã tạo người dùng mẫu.")

        # Tạo trung tâm y tế
        mc1 = MedicalCenter(name='Bệnh viện Đa khoa Quốc tế', address='123 Đường ABC, Quận 1', phone='0281234567',
                            description='Bệnh viện hàng đầu TP.HCM')
        mc2 = MedicalCenter(name='Phòng khám Chuyên khoa Răng Hàm Mặt', address='456 Đường XYZ, Quận 3',
                            phone='0289876543', description='Chuyên khoa răng hàm mặt uy tín')
        db.session.add_all([mc1, mc2])
        db.session.commit()
        print("Đã tạo trung tâm y tế mẫu.")

        # Tạo các khoa
        dep1 = Department(name='Khoa Tim mạch', description='Chuyên khám và điều trị bệnh tim')
        dep2 = Department(name='Khoa Da liễu', description='Chuyên khám và điều trị bệnh ngoài da')
        dep3 = Department(name='Khoa Nhi', description='Chuyên khám và điều trị cho trẻ em')
        db.session.add_all([dep1, dep2, dep3])
        db.session.commit()
        print("Đã tạo các khoa mẫu.")

        # Gán bác sĩ vào khoa và trung tâm y tế
        dd1 = DoctorDepartment(doctor_id=doctor1.id, department_id=dep1.id)
        dd2 = DoctorDepartment(doctor_id=doctor2.id, department_id=dep2.id)
        dd3 = DoctorDepartment(doctor_id=doctor3.id, department_id=dep1.id)
        dd4 = DoctorDepartment(doctor_id=doctor4.id, department_id=dep3.id)
        db.session.add_all([dd1, dd2, dd3, dd4])

        dmc1 = DoctorMedicalCenter(doctor_id=doctor1.id, medical_center_id=mc1.id)
        dmc2 = DoctorMedicalCenter(doctor_id=doctor2.id, medical_center_id=mc1.id)
        dmc3 = DoctorMedicalCenter(doctor_id=doctor3.id, medical_center_id=mc2.id)
        dmc4 = DoctorMedicalCenter(doctor_id=doctor4.id, medical_center_id=mc1.id)
        db.session.add_all([dmc1, dmc2, dmc3, dmc4])
        db.session.commit()
        print("Đã gán bác sĩ vào khoa và trung tâm y tế.")

        # Tạo ca làm việc (Shift) cho bác sĩ
        today = date.today()
        tomorrow = today + timedelta(days=1)
        day_after_tomorrow = today + timedelta(days=2)

        s1 = Shift(doctor_id=doctor1.id, medical_center_id=mc1.id, work_date=today, start_time=time(8, 0),
                   end_time=time(12, 0), max_patients=10, current_patients=0)
        s2 = Shift(doctor_id=doctor1.id, medical_center_id=mc1.id, work_date=today, start_time=time(13, 0),
                   end_time=time(17, 0), max_patients=10, current_patients=0)
        s3 = Shift(doctor_id=doctor2.id, medical_center_id=mc1.id, work_date=tomorrow, start_time=time(9, 0),
                   end_time=time(12, 0), max_patients=10, current_patients=0)
        s4 = Shift(doctor_id=doctor3.id, medical_center_id=mc2.id, work_date=day_after_tomorrow, start_time=time(14, 0),
                   end_time=time(18, 0), max_patients=10, current_patients=0)
        db.session.add_all([s1, s2, s3, s4])
        db.session.commit()
        print("Đã tạo ca làm việc mẫu.")

        # Tạo một vé đặt lịch mẫu để kiểm tra trang payment
        ticket1 = Ticket(
            uuid="ticket-sample-12345",
            shifts_id=s1.id,
            client_id=client1.id,
            status="pending",
            first_name=client1.first_name,
            last_name=client1.last_name,
            birth_of_day=date(1995, 5, 10),
            gender="Male",
            appointment_time=s1.start_time
        )
        db.session.add(ticket1)
        db.session.commit()
        print(f"Đã tạo vé đặt lịch mẫu với ID: {ticket1.id}")
        print("\n--- Hoàn thành tạo dữ liệu mẫu ---")