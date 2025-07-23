from sqlalchemy import Column, Integer, String, DateTime, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
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
    ships = relationship("Ship", back_populates="doctor")
    tickets_as_client = relationship("Ticket", back_populates="client", foreign_keys="Ticket.client_id")

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

class Ship(BaseModel):
    __tablename__ = 'ships'
    doctor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    work_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    doctor = relationship("User", back_populates="ships")
    tickets = relationship("Ticket", back_populates="ship")

    def __str__(self):
        return f"Ship for {self.doctor_id} on {self.work_date}"

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
    ship_id = Column(Integer, ForeignKey('ships.id'), nullable=False)
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
    ship = relationship("Ship", back_populates="tickets")
    client = relationship("User", back_populates="tickets_as_client", foreign_keys=[client_id])

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Clear existing data to avoid duplicates
        db.create_all()

        # Check if users already exist to avoid duplicates
        if not User.query.filter_by(username="admin1").first():
            users = [
                User(username="admin1", password="admin123", role=UserRole.ADMIN.value, first_name="Admin", last_name="User"),
                User(username="client1", password="client123", role=UserRole.USER.value, first_name="John", last_name="Doe"),
                User(username="doctor1", password="doc123", role=UserRole.DOCTOR.value, first_name="Nguyen", last_name="Van A", avatar='https://res.cloudinary.com/du6rdcpyi/image/upload/v1753201720/ke3ntry60qmna9ijxsje.jpg'),
                User(username="doctor2", password="doc456", role=UserRole.DOCTOR.value, first_name="Tran", last_name="Thi B", avatar='https://res.cloudinary.com/du6rdcpyi/image/upload/v1753201802/dcqs2vrao4xukk70cjl8.jpg')
            ]
            db.session.bulk_save_objects(users)
            db.session.commit()

        # Check if departments already exist
        if not Department.query.filter_by(slug="tim-mach").first():
            departments = [
                Department(name="Tim mạch", slug="tim-mach", symbol_img="tim_mach.png"),
                Department(name="Nội khoa", slug="noi-khoa", symbol_img="noi_khoa.png")
            ]
            db.session.bulk_save_objects(departments)
            db.session.commit()

        # Check if medical centers already exist
        if not MedicalCenter.query.filter_by(name="Bệnh Viện Chợ Rẫy").first():
            medical_centers = [
                MedicalCenter(name="Bệnh Viện Chợ Rẫy", description="Bệnh viện lớn tại TP.HCM", cover_img="https://res.cloudinary.com/du6rdcpyi/image/upload/v1753201863/ck97elfnedtfpacuzcds.png"),
                MedicalCenter(name="Bệnh Viện Bạch Mai", description="Bệnh viện lớn tại Hà Nội", cover_img="https://res.cloudinary.com/du6rdcpyi/image/upload/v1753201879/s2oajgfxqgmgfudool9m.jpg")
            ]
            db.session.bulk_save_objects(medical_centers)
            db.session.commit()

        # Check if doctor-department relationships exist
        if not DoctorDepartment.query.filter_by(user_id=3, department_id=1).first():
            doctor_departments = [
                DoctorDepartment(user_id=3, department_id=1),  # Doctor1 in Tim mạch
                DoctorDepartment(user_id=4, department_id=2)   # Doctor2 in Nội khoa
            ]
            db.session.bulk_save_objects(doctor_departments)
            db.session.commit()

        # Check if medical center-department relationships exist
        if not MedicalCenterDepartment.query.filter_by(medical_center_id=1, department_id=1).first():
            medical_center_departments = [
                MedicalCenterDepartment(medical_center_id=1, department_id=1),  # Chợ Rẫy - Tim mạch
                MedicalCenterDepartment(medical_center_id=2, department_id=2)   # Bạch Mai - Nội khoa
            ]
            db.session.bulk_save_objects(medical_center_departments)
            db.session.commit()

        # Check if doctor-medical center relationships exist
        if not DoctorMedicalCenter.query.filter_by(user_id=3, medical_center_id=1).first():
            doctor_medical_centers = [
                DoctorMedicalCenter(user_id=3, medical_center_id=1),  # Doctor1 at Chợ Rẫy
                DoctorMedicalCenter(user_id=4, medical_center_id=2)   # Doctor2 at Bạch Mai
            ]
            db.session.bulk_save_objects(doctor_medical_centers)
            db.session.commit()

        # Check if ships exist
        if not Ship.query.filter_by(doctor_id=3).first():
            ships = [
                Ship(doctor_id=3, start_time="09:00", end_time="12:00", work_date="2025-07-23"),
                Ship(doctor_id=3, start_time="14:00", end_time="17:00", work_date="2025-07-23"),
                Ship(doctor_id=4, start_time="10:00", end_time="13:00", work_date="2025-07-23")
            ]
            db.session.bulk_save_objects(ships)
            db.session.commit()

        # Check if tickets exist
        if not Ticket.query.filter_by(uuid="ticket-001").first():
            tickets = [
                Ticket(uuid="ticket-001", ship_id=1, client_id=2, status="pending", first_name="John", last_name="Doe",
                       birth_of_day="1990-01-01", gender="Male", appointment_time="09:30")
            ]
            db.session.bulk_save_objects(tickets)
            db.session.commit()

        print("Sample data inserted successfully!")