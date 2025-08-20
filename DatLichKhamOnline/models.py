import hashlib
import uuid
from datetime import datetime, time
from enum import Enum as PyEnum
from typing import List

from sqlalchemy import String, Date, Time, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from DatLichKhamOnline import app, db


class Base(db.DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)


class UserRole(PyEnum):
    ADMIN = "admin"
    USER = "user"
    DOCTOR = "doctor"


class TicketStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class User(BaseModel):
    __tablename__ = 'users'
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    role: Mapped[UserRole]
    username: Mapped[str] = mapped_column(String(80), unique=True)
    first_name: Mapped[str] = mapped_column(db.String(50))
    last_name: Mapped[str] = mapped_column(db.String(50))
    birth_of_day: Mapped[Date] = mapped_column(db.Date, nullable=True)
    gender: Mapped[str] = mapped_column(db.String(10), nullable=True)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=True)
    address: Mapped[str] = mapped_column(db.String(200), nullable=True)
    avatar: Mapped[str] = mapped_column(db.String(255), nullable=True)

    doctor: Mapped["Doctor"] = relationship(back_populates="user")
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="client")

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @staticmethod
    def hash_password(password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    def check_password(self, password):
        return self.password == self.hash_password(password)


class MedicalCenter(BaseModel):
    __tablename__ = 'medical_centers'
    name: Mapped[str] = mapped_column(db.String(255))
    address: Mapped[str] = mapped_column(db.String(255), nullable=True)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=True)
    description: Mapped[str] = mapped_column(db.String(255), nullable=True)
    image: Mapped[str] = mapped_column(db.String(255), nullable=True)

    doctors: Mapped[List["Doctor"]] = relationship(back_populates="medical_center")

    def __str__(self):
        return self.name


class Department(BaseModel):
    __tablename__ = 'departments'
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    doctor_departments: Mapped[List["DoctorDepartment"]] = relationship(back_populates="department")

    def __str__(self):
        return self.name


class Doctor(BaseModel):
    __tablename__ = 'doctors'
    id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    medical_center_id = mapped_column(ForeignKey('medical_centers.id'), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="doctor")
    medical_center: Mapped[MedicalCenter] = relationship(back_populates="doctors")
    doctor_departments: Mapped[List["DoctorDepartment"]] = relationship(back_populates="doctor")
    doctor_shifts: Mapped[List["DoctorShift"]] = relationship(back_populates="doctor")


class DoctorDepartment(BaseModel):
    __tablename__ = 'doctor_departments'
    doctor_id: Mapped[int] = mapped_column(ForeignKey('doctors.id'))
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))

    doctor: Mapped[Doctor] = relationship(back_populates="doctor_departments")
    department: Mapped[Department] = relationship(back_populates="doctor_departments")


class Shift(BaseModel):
    __tablename__ = 'shifts'
    start_time: Mapped[Time] = mapped_column(db.Time)
    end_time: Mapped[Time] = mapped_column(db.Time)

    doctor_shifts: Mapped[List["DoctorShift"]] = relationship(back_populates="shift")


class DoctorShift(BaseModel):
    __tablename__ = 'doctor_shifts'
    doctor_id: Mapped[int] = mapped_column(ForeignKey('doctors.id'))
    shift_id: Mapped[int] = mapped_column(ForeignKey('shifts.id'))
    work_date: Mapped[Date] = mapped_column(db.Date)

    doctor: Mapped[Doctor] = relationship(back_populates="doctor_shifts")
    shift: Mapped[Shift] = relationship(back_populates="doctor_shifts")
    ticket: Mapped["Ticket"] = relationship(back_populates="doctor_shift")


class Ticket(BaseModel):
    __tablename__ = 'tickets'
    uuid: Mapped[str] = mapped_column(db.String(255), unique=True, default=uuid.uuid4())
    doctor_shift_id: Mapped[int] = mapped_column(ForeignKey('doctor_shifts.id'), unique=True)
    client_id: Mapped[int] = mapped_column(db.Integer, ForeignKey('users.id'))
    status: Mapped[TicketStatus]
    first_name: Mapped[str] = mapped_column(db.String(255))
    last_name: Mapped[str] = mapped_column(db.String(255))
    birth_of_day: Mapped[Date] = mapped_column(db.Date)
    gender: Mapped[str] = mapped_column(db.String(50))

    doctor_shift: Mapped[DoctorShift] = relationship(back_populates="ticket")
    client: Mapped[User] = relationship(back_populates="tickets")


if __name__ == '__main__':
    with app.app_context():
        print("Đang xóa và tạo lại các bảng...")
        Base.metadata.drop_all(db.engine)
        Base.metadata.create_all(db.engine)
        print("Hoàn tất!")

        print("\n--- Đang tạo dữ liệu mẫu ---")

        # # Tạo người dùng mẫu: băm mật khẩu bằng MD5
        admin_user = User(username='admin', password=User.hash_password('123'), email='admin@example.com',
                          role=UserRole.ADMIN.value, first_name='Admin', last_name='System')
        u1 = User(username='doc1', password=User.hash_password('123'), email='doctor1@example.com',
                  role=UserRole.DOCTOR.value, first_name='Lâm Việt', last_name='Trung')
        u2 = User(username='doc2', password=User.hash_password('123'), email='doctor2@example.com',
                  role=UserRole.DOCTOR.value, first_name='Phạm Thị', last_name='Mai')
        u3 = User(username='doc3', password=User.hash_password('123'), email='doctor3@example.com',
                  role=UserRole.DOCTOR.value, first_name='Lê Văn', last_name='Dũng')
        u4 = User(username='doc4', password=User.hash_password('123'), email='doctor4@example.com',
                  role=UserRole.DOCTOR.value, first_name='Trần Thị', last_name='Hương')
        u5 = User(username='client1', password=User.hash_password('123'), email='client1@example.com',
                  role=UserRole.USER.value, first_name='Khách', last_name='Hàng A')

        db.session.add_all([admin_user, u1, u2, u3, u4, u5])
        db.session.commit()

        # Tạo trung tâm y tế
        mc1 = MedicalCenter(name='Bệnh viện Đa khoa Quốc tế', address='123 Đường ABC, Quận 1', phone='0281234567',
                            description='Bệnh viện hàng đầu TP.HCM')
        mc2 = MedicalCenter(name='Phòng khám Chuyên khoa Răng Hàm Mặt', address='456 Đường XYZ, Quận 3',
                            phone='0289876543', description='Chuyên khoa răng hàm mặt uy tín')
        db.session.add_all([mc1, mc2])
        db.session.commit()

        # Tạo các khoa
        dep1 = Department(name='Khoa Tim mạch', description='Chuyên khám và điều trị bệnh tim')
        dep2 = Department(name='Khoa Da liễu', description='Chuyên khám và điều trị bệnh ngoài da')
        dep3 = Department(name='Khoa Nhi', description='Chuyên khám và điều trị cho trẻ em')
        db.session.add_all([dep1, dep2, dep3])
        db.session.commit()

        d1 = Doctor(id=u1.id, medical_center_id=mc1.id)
        d2 = Doctor(id=u2.id, medical_center_id=mc2.id)
        d3 = Doctor(id=u3.id, medical_center_id=mc1.id)
        d4 = Doctor(id=u4.id, medical_center_id=mc2.id)
        db.session.add_all([d1, d2, d3, d4])
        db.session.commit()

        dd1 = DoctorDepartment(doctor_id=d1.id, department_id=dep1.id)
        dd2 = DoctorDepartment(doctor_id=d2.id, department_id=dep2.id)
        dd3 = DoctorDepartment(doctor_id=d3.id, department_id=dep1.id)
        dd4 = DoctorDepartment(doctor_id=d4.id, department_id=dep3.id)
        db.session.add_all([dd1, dd2, dd3, dd4])
        db.session.commit()

        # Tạo các ca (cố định)
        shift1 = Shift(start_time=time(7, 0), end_time=time(7, 30))
        shift2 = Shift(start_time=time(7, 30), end_time=time(8, 0))
        shift3 = Shift(start_time=time(8, 0), end_time=time(8, 30))
        shift4 = Shift(start_time=time(8, 30), end_time=time(9, 0))
        shift5 = Shift(start_time=time(9, 0), end_time=time(9, 30))
        shift6 = Shift(start_time=time(9, 30), end_time=time(10, 0))
        shift7 = Shift(start_time=time(10, 0), end_time=time(10, 30))
        shift8 = Shift(start_time=time(10, 30), end_time=time(11, 0))
        shift9 = Shift(start_time=time(11, 0), end_time=time(11, 30))
        shift10 = Shift(start_time=time(11, 30), end_time=time(12, 0))
        shift11 = Shift(start_time=time(12, 0), end_time=time(12, 30))
        shift12 = Shift(start_time=time(12, 30), end_time=time(13, 0))
        shift13 = Shift(start_time=time(13, 0), end_time=time(13, 30))
        shift14 = Shift(start_time=time(13, 30), end_time=time(14, 0))
        shift15 = Shift(start_time=time(14, 0), end_time=time(14, 30))
        shift16 = Shift(start_time=time(14, 30), end_time=time(15, 0))
        shift17 = Shift(start_time=time(15, 0), end_time=time(15, 30))
        shift18 = Shift(start_time=time(15, 30), end_time=time(16, 0))
        shift19 = Shift(start_time=time(16, 0), end_time=time(16, 30))
        shift20 = Shift(start_time=time(16, 30), end_time=time(17, 0))
        shift21 = Shift(start_time=time(17, 0), end_time=time(17, 30))
        shift22 = Shift(start_time=time(17, 30), end_time=time(18, 0))

        db.session.add_all([
            shift1, shift2, shift3, shift4, shift5, shift6, shift7, shift8, shift9, shift10,
            shift11, shift12, shift13, shift14, shift15, shift16, shift17, shift18, shift19, shift20,
            shift21, shift22
        ])
        db.session.commit()

        ds1 = DoctorShift(doctor_id=d1.id, shift_id=shift1.id, work_date=datetime.now().date())
        ds2 = DoctorShift(doctor_id=d1.id, shift_id=shift2.id, work_date=datetime.now().date())
        ds3 = DoctorShift(doctor_id=d1.id, shift_id=shift3.id, work_date=datetime.now().date())
        ds4 = DoctorShift(doctor_id=d2.id, shift_id=shift1.id, work_date=datetime.now().date())
        ds5 = DoctorShift(doctor_id=d2.id, shift_id=shift2.id, work_date=datetime.now().date())
        ds6 = DoctorShift(doctor_id=d2.id, shift_id=shift3.id, work_date=datetime.now().date())
        ds7 = DoctorShift(doctor_id=d3.id, shift_id=shift1.id, work_date=datetime.now().date())
        ds8 = DoctorShift(doctor_id=d3.id, shift_id=shift2.id, work_date=datetime.now().date())
        ds9 = DoctorShift(doctor_id=d3.id, shift_id=shift3.id, work_date=datetime.now().date())
        ds10 = DoctorShift(doctor_id=d4.id, shift_id=shift1.id, work_date=datetime.now().date())
        ds11 = DoctorShift(doctor_id=d4.id, shift_id=shift2.id, work_date=datetime.now().date())
        ds12 = DoctorShift(doctor_id=d4.id, shift_id=shift3.id, work_date=datetime.now().date())
        db.session.add_all([ds1, ds2, ds3, ds4, ds5, ds6, ds7, ds8, ds9, ds10, ds11, ds12])
        db.session.commit()

        ticket = Ticket(client_id=u5.id, doctor_shift_id=ds1.id, status=TicketStatus.PENDING.value, first_name='Hien', last_name='Trung', birth_of_day=datetime.now().date(), gender='Nam')
        db.session.add(ticket)
        db.session.commit()

        print("\n--- Hoàn thành tạo dữ liệu mẫu ---")
