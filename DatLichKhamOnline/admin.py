from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask import redirect, url_for, request
from flask_login import current_user
from models import User, Doctor, MedicalCenter, Department, Shift, UserRole, Ticket, TicketStatus
from DatLichKhamOnline import app, db


# Lớp tùy chỉnh cho trang chủ admin để hiển thị thống kê
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        # Chỉ admin mới được truy cập
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            return redirect(url_for('user_login'))

        # Truy vấn các số liệu thống kê
        stats = {
            'user_count': db.session.query(User).count(),
            'doctor_count': db.session.query(User).filter_by(role=UserRole.DOCTOR).count(),
            'ticket_count': db.session.query(Ticket).count(),
            'pending_tickets': db.session.query(Ticket).filter_by(status=TicketStatus.PENDING).count()
        }

        return self.render('admin/index.html', stats=stats)


# Lớp tùy chỉnh để bảo mật các trang admin khác
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('user_login', next=request.url))


# Tạo các lớp View tùy chỉnh cho từng Model
class UserAdminView(SecureModelView):
    column_list = ('id', 'username', 'email', 'first_name', 'last_name', 'role')
    column_searchable_list = ('username', 'email', 'first_name', 'last_name')
    column_filters = ('role',)
    column_labels = dict(username='Tên đăng nhập', email='Email', first_name='Họ đệm', last_name='Tên', role='Vai trò')
    form_columns = ('username', 'password', 'email', 'first_name', 'last_name', 'role', 'avatar')


class MedicalCenterAdminView(SecureModelView):
    column_list = ('name', 'address', 'phone')
    column_searchable_list = ('name', 'address')
    column_labels = dict(name='Tên trung tâm', address='Địa chỉ', phone='Số điện thoại', description='Mô tả',
                         image='Ảnh bìa')
    form_columns = ('name', 'address', 'phone', 'description', 'image')


class DoctorAdminView(SecureModelView):
    column_list = ('user', 'medical_center', 'start_year')
    column_labels = dict(user='Bác sĩ (User)', medical_center='Nơi công tác', start_year='Năm bắt đầu làm việc',
                         description='Mô tả kinh nghiệm')
    form_columns = ('user', 'medical_center', 'description', 'start_year')


class DepartmentAdminView(SecureModelView):
    column_list = ('name', 'description')
    column_labels = dict(name='Tên khoa', description='Mô tả')


# =======================================================
# LỚP VIEW TÙY CHỈNH CHO PHIẾU KHÁM (TICKET)
# =======================================================
class TicketAdminView(SecureModelView):
    # Các cột sẽ hiển thị trong danh sách
    column_list = (
        'uuid',
        'client',  # Hiển thị tên bệnh nhân (User) thay vì client_id
        'doctor_shift.doctor.user',  # Đi sâu vào relationship để lấy tên bác sĩ
        'doctor_shift.work_date',
        'doctor_shift.shift.start_time',
        'status'
    )

    # Các cột có thể lọc
    column_filters = ('status', 'doctor_shift.work_date')

    # Đặt lại tên hiển thị cho các cột
    column_labels = {
        'uuid': 'Mã Vé',
        'client': 'Tên Bệnh Nhân',
        'doctor_shift.doctor.user': 'Tên Bác Sĩ',
        'doctor_shift.work_date': 'Ngày Khám',
        'doctor_shift.shift.start_time': 'Giờ Khám',
        'status': 'Trạng Thái'
    }


# Khởi tạo đối tượng Admin với trang chủ tùy chỉnh
admin = Admin(app, name='QUẢN TRỊ WEBSITE', template_mode='bootstrap4', index_view=MyAdminIndexView())

# Thêm các View đã được tùy chỉnh vào trang admin
admin.add_view(UserAdminView(User, db.session, name='Người dùng'))
admin.add_view(DoctorAdminView(Doctor, db.session, name='Hồ sơ Bác sĩ'))
admin.add_view(MedicalCenterAdminView(MedicalCenter, db.session, name='Trung tâm y tế'))
admin.add_view(DepartmentAdminView(Department, db.session, name='Chuyên khoa'))
admin.add_view(SecureModelView(Shift, db.session, name='Ca làm việc'))
admin.add_view(TicketAdminView(Ticket, db.session, name='Phiếu khám'))  # SỬ DỤNG TICKETADMINVIEW MỚI