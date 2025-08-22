import hashlib
import uuid
from datetime import datetime, time, timedelta, date
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
    start_year: Mapped[int] = mapped_column(db.Integer, nullable=True)

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
    ticket: Mapped["Ticket"] = relationship(back_populates="doctor_shift", uselist=False)


class Ticket(BaseModel):
    __tablename__ = 'tickets'
    uuid: Mapped[str] = mapped_column(db.String(255), unique=True, default=lambda: str(uuid.uuid4()))
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

        # 1. TẠO TẤT CẢ USER TRƯỚC
        print("-> Đang tạo người dùng...")
        admin_user = User(username='admin', password=User.hash_password('123'), email='admin@example.com',
                          role=UserRole.ADMIN, first_name='Admin', last_name='System')
        u1 = User(username='doc1', password=User.hash_password('123'), email='doctor1@example.com',
                  role=UserRole.DOCTOR, first_name='Lâm Việt', last_name='Trung')
        u2 = User(username='doc2', password=User.hash_password('123'), email='doctor2@example.com',
                  role=UserRole.DOCTOR, first_name='Phạm Thị', last_name='Mai')
        u3 = User(username='doc3', password=User.hash_password('123'), email='doctor3@example.com',
                  role=UserRole.DOCTOR, first_name='Lê Văn', last_name='Dũng')
        u4 = User(username='doc4', password=User.hash_password('123'), email='doctor4@example.com',
                  role=UserRole.DOCTOR, first_name='Trần Thị', last_name='Hương')
        u5 = User(username='client1', password=User.hash_password('123'), email='client1@example.com',
                  role=UserRole.USER, first_name='Khách', last_name='Hàng A')
        db.session.add_all([admin_user, u1, u2, u3, u4, u5])
        db.session.commit()

        # 2. TẠO CÁC THÔNG TIN CHUNG
        print("-> Đang tạo trung tâm y tế và khoa...")
        mc1 = MedicalCenter(name='Bệnh viện Đa khoa Quốc tế', address='123 Đường ABC, Quận 1', phone='0281234567',
                            description='Bệnh viện hàng đầu TP.HCM')
        mc2 = MedicalCenter(name='Phòng khám Răng Hàm Mặt', address='456 Đường XYZ, Quận 3', phone='0289876543',
                            description='Chuyên khoa răng hàm mặt uy tín')
        db.session.add_all([mc1, mc2])

        dep1 = Department(name='Khoa Tim mạch')
        dep2 = Department(name='Khoa Da liễu')
        dep3 = Department(name='Khoa Nhi')
        db.session.add_all([dep1, dep2, dep3])
        db.session.commit()

        # 3. TẠO DOCTOR SAU KHI ĐÃ CÓ USER
        print("-> Đang tạo hồ sơ bác sĩ...")
        d1 = Doctor(id=u1.id, medical_center_id=mc1.id, start_year=2010)
        d2 = Doctor(id=u2.id, medical_center_id=mc2.id, start_year=2005)
        d3 = Doctor(id=u3.id, medical_center_id=mc1.id, start_year=2015)
        d4 = Doctor(id=u4.id, medical_center_id=mc2.id, start_year=2018)
        db.session.add_all([d1, d2, d3, d4])
        db.session.commit()

        # 4. TẠO CÁC BẢNG LIÊN KẾT (DOCTORDEPARTMENT)
        print("-> Đang liên kết bác sĩ với khoa...")
        dd1 = DoctorDepartment(doctor_id=d1.id, department_id=dep1.id)
        dd2 = DoctorDepartment(doctor_id=d2.id, department_id=dep2.id)
        dd3 = DoctorDepartment(doctor_id=d3.id, department_id=dep1.id)
        dd4 = DoctorDepartment(doctor_id=d4.id, department_id=dep3.id)
        db.session.add_all([dd1, dd2, dd3, dd4])
        db.session.commit()

        # 5. TẠO CÁC CA LÀM VIỆC
        print("-> Đang tạo các ca làm việc...")
        shifts = []
        for hour in range(7, 23):
            shifts.append(Shift(start_time=time(hour, 0), end_time=time(hour, 30)))
            shifts.append(Shift(start_time=time(hour, 30), end_time=time(hour + 1, 0)))
        db.session.add_all(shifts)
        db.session.commit()

        # 6. TẠO LỊCH LÀM VIỆC VÀ VÉ MẪU
        print("-> Đang tạo lịch làm việc và vé mẫu...")
        today = datetime.now().date()
        ds1 = DoctorShift(doctor_id=d1.id, shift_id=shifts[0].id, work_date=today)
        ds2 = DoctorShift(doctor_id=d1.id, shift_id=shifts[1].id, work_date=today)
        db.session.add_all([ds1, ds2])
        db.session.commit()

        ticket1 = Ticket(doctor_shift_id=ds1.id, client_id=u5.id, status=TicketStatus.CONFIRMED, first_name="An",
                         last_name="Nguyễn", birth_of_day=date(1990, 5, 15), gender="Nữ")
        db.session.add(ticket1)
        db.session.commit()

        print("\n--- Hoàn thành tạo dữ liệu mẫu ---")
