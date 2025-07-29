from sqlalchemy import Column, Integer, String, DateTime, Date, Time, ForeignKey
from sqlalchemy.orm import relationship, backref
from datetime import datetime, time, timedelta, date
from enum import Enum as UserEnum
from DatLichKhamOnline import app, db


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class UserRole(UserEnum):
    ADMIN = "admin"
    USER = "user"
    DOCTOR = "doctor"


class User(BaseModel):
    __tablename__ = 'users'
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    middle_name = Column(String(255))
    avatar = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor_departments = relationship("DoctorDepartment", back_populates="user")
    doctor_medical_centers = relationship("DoctorMedicalCenter", back_populates="user")
    shifts = relationship("Shift", back_populates="doctor")  # Corrected from 'shift' to 'shifts'
    tickets_as_client = relationship("Ticket", back_populates="client", foreign_keys="Ticket.client_id")

    # Thêm relationships để dễ dàng truy cập chuyên khoa và nơi công tác
    specialties = relationship("Department", secondary="doctor_department", viewonly=True)
    work_places = relationship("MedicalCenter", secondary="doctor_medical_center", viewonly=True)

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class Department(BaseModel):
    __tablename__ = 'departments'
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    symbol_img = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    doctor_departments = relationship("DoctorDepartment", back_populates="department")
    medical_center_departments = relationship("MedicalCenterDepartment", back_populates="department")

    def __str__(self):
        return self.name


class MedicalCenter(BaseModel):
    __tablename__ = 'medical_centers'
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    cover_img = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor_medical_centers = relationship("DoctorMedicalCenter", back_populates="medical_center")
    medical_center_departments = relationship("MedicalCenterDepartment", back_populates="medical_center")

    def __str__(self):
        return self.name


class DoctorDepartment(BaseModel):
    __tablename__ = 'doctor_department'
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)

    # Relationships
    user = relationship("User", back_populates="doctor_departments")
    department = relationship("Department", back_populates="doctor_departments")


class MedicalCenterDepartment(BaseModel):
    __tablename__ = 'medical_center_department'
    medical_center_id = Column(Integer, ForeignKey('medical_centers.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)

    # Relationships
    medical_center = relationship("MedicalCenter", back_populates="medical_center_departments")
    department = relationship("Department", back_populates="medical_center_departments")


class Shift(BaseModel):
    __tablename__ = 'shifts'
    doctor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    work_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    doctor = relationship("User", back_populates="shifts")  # Corrected: 'shifts'
    tickets = relationship("Ticket", back_populates="shift")

    def __str__(self):
        return f"Shift for {self.doctor_id} on {self.work_date}"


class DoctorMedicalCenter(BaseModel):
    __tablename__ = 'doctor_medical_center'
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    medical_center_id = Column(Integer, ForeignKey('medical_centers.id'), nullable=False)

    # Relationships
    user = relationship("User", back_populates="doctor_medical_centers")
    medical_center = relationship("MedicalCenter", back_populates="doctor_medical_centers")


class Ticket(BaseModel):
    __tablename__ = 'tickets'
    uuid = Column(String(255), nullable=False, unique=True)
    shifts_id = Column(Integer, ForeignKey('shifts.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(50), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    birth_of_day = Column(Date, nullable=False)
    gender = Column(String(50), nullable=False)
    appointment_time = Column(Time, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_on = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shift = relationship("Shift", back_populates="tickets")
    client = relationship("User", back_populates="tickets_as_client", foreign_keys=[client_id])


if __name__ == '__main__':
    with app.app_context():
        # Xóa tất cả các bảng hiện có và tạo lại
        print("Đang xóa và tạo lại các bảng...")
        db.drop_all()
        db.create_all()
        print("Hoàn tất!")

        print("\n--- Đang tạo dữ liệu mẫu ---")

        # 1. Tạo người dùng mẫu: 1 admin, 4 bác sĩ, 1 người dùng
        admin_user = User(username='admin', password='123', role=UserRole.ADMIN.value, first_name='Admin',
                          last_name='System')
        doctor1 = User(username='doc1', password='123', role=UserRole.DOCTOR.value, first_name='Lâm Việt',
                       last_name='Trung')
        doctor2 = User(username='doc2', password='123', role=UserRole.DOCTOR.value, first_name='Phạm Thị',
                       last_name='Mai')
        doctor3 = User(username='doc3', password='123', role=UserRole.DOCTOR.value, first_name='Lê Văn',
                       last_name='Dũng')
        doctor4 = User(username='doc4', password='123', role=UserRole.DOCTOR.value, first_name='Trần Thị',
                       last_name='Hương')
        client1 = User(username='client1', password='123', role=UserRole.USER.value, first_name='Khách',
                       last_name='Hàng A')

        db.session.add_all([admin_user, doctor1, doctor2, doctor3, doctor4, client1])
        db.session.commit()
        print("Đã tạo người dùng mẫu.")

        # 2. Tạo khoa mẫu
        cardiology_dept = Department(name='Tim mạch', slug='tim-mach')
        pediatrics_dept = Department(name='Nhi khoa', slug='nhi-khoa')
        general_med_dept = Department(name='Nội tổng quát', slug='noi-tong-quat')
        dermatology_dept = Department(name='Da liễu', slug='da-lieu')

        db.session.add_all([cardiology_dept, pediatrics_dept, general_med_dept, dermatology_dept])
        db.session.commit()
        print("Đã tạo khoa mẫu.")

        # 3. Tạo trung tâm y tế mẫu
        medical_center_a = MedicalCenter(name='Bệnh viện Chợ Rẫy', description='Bệnh viện đa khoa tuyến cuối')
        medical_center_b = MedicalCenter(name='Bệnh viện Nhi Đồng 1', description='Bệnh viện chuyên khoa nhi')
        medical_center_c = MedicalCenter(name='Phòng khám Đa khoa Quốc tế',
                                         description='Phòng khám cung cấp dịch vụ tổng quát')
        medical_center_d = MedicalCenter(name='Bệnh viện Da Liễu TP.HCM', description='Bệnh viện chuyên khoa da liễu')

        db.session.add_all([medical_center_a, medical_center_b, medical_center_c, medical_center_d])
        db.session.commit()
        print("Đã tạo trung tâm y tế mẫu.")

        # 4. Liên kết bác sĩ với khoa và trung tâm y tế
        doc_dept1 = DoctorDepartment(user_id=doctor1.id, department_id=cardiology_dept.id)
        doc_mc1 = DoctorMedicalCenter(user_id=doctor1.id, medical_center_id=medical_center_a.id)
        doc_dept2 = DoctorDepartment(user_id=doctor2.id, department_id=pediatrics_dept.id)
        doc_mc2 = DoctorMedicalCenter(user_id=doctor2.id, medical_center_id=medical_center_b.id)
        doc_dept3 = DoctorDepartment(user_id=doctor3.id, department_id=general_med_dept.id)
        doc_mc3 = DoctorMedicalCenter(user_id=doctor3.id, medical_center_id=medical_center_c.id)
        doc_dept4 = DoctorDepartment(user_id=doctor4.id, department_id=dermatology_dept.id)
        doc_mc4 = DoctorMedicalCenter(user_id=doctor4.id, medical_center_id=medical_center_d.id)

        mc_dept1 = MedicalCenterDepartment(medical_center_id=medical_center_a.id, department_id=cardiology_dept.id)
        mc_dept2 = MedicalCenterDepartment(medical_center_id=medical_center_b.id, department_id=pediatrics_dept.id)
        mc_dept3 = MedicalCenterDepartment(medical_center_id=medical_center_c.id, department_id=general_med_dept.id)
        mc_dept4 = MedicalCenterDepartment(medical_center_id=medical_center_d.id, department_id=dermatology_dept.id)

        db.session.add_all([doc_dept1, doc_mc1, doc_dept2, doc_mc2, doc_dept3, doc_mc3, doc_dept4, doc_mc4,
                            mc_dept1, mc_dept2, mc_dept3, mc_dept4])
        db.session.commit()
        print("Đã thiết lập các mối quan hệ.")

        print("\n--- Đang tạo lịch làm việc cho các bác sĩ để phủ 24h đến 15/08/2025 ---")

        start_date = date.today()
        end_date = date(2025, 8, 15)
        delta = timedelta(days=1)
        current_date = start_date

        while current_date <= end_date:
            # Ca 1: 00:00 - 06:00 (Bác sĩ 1)
            shift1 = Shift(
                doctor_id=doctor1.id,
                start_time=time(0, 0),  # 00:00 AM
                end_time=time(6, 0),  # 06:00 AM
                work_date=current_date
            )

            # Ca 2: 06:00 - 12:00 (Bác sĩ 2)
            shift2 = Shift(
                doctor_id=doctor2.id,
                start_time=time(6, 0),  # 06:00 AM
                end_time=time(12, 0),  # 12:00 PM
                work_date=current_date
            )

            # Ca 3: 12:00 - 18:00 (Bác sĩ 3)
            shift3 = Shift(
                doctor_id=doctor3.id,
                start_time=time(12, 0),  # 12:00 PM
                end_time=time(18, 0),  # 06:00 PM
                work_date=current_date
            )

            # Ca 4: 18:00 - 00:00 (Bác sĩ 4) - kết thúc vào nửa đêm của ngày hiện tại
            shift4 = Shift(
                doctor_id=doctor4.id,
                start_time=time(18, 0),  # 06:00 PM
                end_time=time(0, 0),  # 00:00 AM của ngày tiếp theo (thực ra là 23:59:59 của ngày hiện tại)
                work_date=current_date
            )

            db.session.add_all([shift1, shift2, shift3, shift4])
            current_date += delta

        db.session.commit()
        print("--- Đã tạo thành công dữ liệu mẫu và lịch làm việc phủ 24h! ---")