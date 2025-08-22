# DatLichKhamOnline/index.py
import uuid
from datetime import datetime, date, time, timedelta

from flask import render_template, request, flash, redirect, url_for, session, \
    g  # Import g để lưu biến global cho request
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.sqltypes import Date

from DatLichKhamOnline import app, db
from models import User, MedicalCenter, DoctorDepartment, Department, Ticket, UserRole, Doctor, DoctorShift, \
    Shift, TicketStatus  # Đảm bảo đã import 'Shift'


# Middleware để tải thông tin người dùng trước mỗi request
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)


@app.route("/")
def home():
    doctors = db.session.query(User).filter(User.role == "doctor").all()
    medical_centers = db.session.query(MedicalCenter).all()
    return render_template('index.html', doctors=doctors, medical_centers=medical_centers)


@app.route("/search")
def search():
    query = request.args.get('q', '').lower()
    doctors = (db.session.query(User).join(Doctor).join(DoctorDepartment).join(Department).filter(
        User.role == "doctor",
        (User.first_name.ilike(f'%{query}%') | User.last_name.ilike(f'%{query}%') | Department.name.ilike(f'%{query}%'))
    ).all())
    medical_centers = db.session.query(MedicalCenter).filter(
        MedicalCenter.name.ilike(f'%{query}%') | MedicalCenter.description.ilike(f'%{query}%')
    ).all()
    return render_template('index.html', doctors=doctors, medical_centers=medical_centers)


@app.route("/search_doctor")
def search_doctor():
    query = request.args.get('q', '').lower()
    doctors = db.session.query(User).join(Doctor).join(DoctorDepartment).join(Department).filter(
        User.role == "doctor",
        (User.first_name.ilike(f'%{query}%') | User.last_name.ilike(f'%{query}%') | Department.name.ilike(f'%{query}%'))
    ).distinct().all()
    return render_template('doctor/doctor_list.html', doctors=doctors)


@app.route("/search_medical_center")
def search_medical_center():
    query = request.args.get('q', '')
    medical_centers = db.session.query(MedicalCenter).filter(
        MedicalCenter.name.ilike(f'%{query}%') | MedicalCenter.description.ilike(f'%{query}%')
    ).all()
    return render_template('hospital/medical_center_list.html', medical_centers=medical_centers)


@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if g.user:
        flash("Bạn đã đăng nhập rồi.", "info")
        return redirect(url_for('home'))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.session.query(User).filter(User.username == username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("home"))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")
    return render_template("user/login.html")


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("Đã đăng xuất.", "success")
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        flash("Bạn đã đăng nhập rồi.", "info")
        return redirect(url_for('home'))

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        username = request.form["username"]
        raw_password = request.form["password"]
        email = request.form["email"]
        avatar = request.form.get("avatar", "default_avatar.jpg")

        if db.session.query(User).filter_by(username=username).first():
            flash("Tên đăng nhập đã tồn tại.", "danger")
            return redirect(url_for("register"))
        if db.session.query(User).filter_by(email=email).first():
            flash("Email đã được sử dụng.", "danger")
            return redirect(url_for("register"))

        new_user = User(first_name=first_name, last_name=last_name, username=username, email=email,
                        password=User.hash_password(raw_password), avatar=avatar, role=UserRole.USER.value)
        db.session.add(new_user)
        db.session.commit()
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("user_login"))
    return render_template("user/register.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if g.user:
        flash("Bạn đã đăng nhập rồi.", "info")
        return redirect(url_for('home'))

    if request.method == "POST":
        email = request.form["email"]
        user = db.session.query(User).filter(User.email == email).first()
        if user:
            flash(
                f"Một liên kết đặt lại mật khẩu đã được gửi đến email của bạn (chức năng này chưa được triển khai).",
                "success")
            return redirect(url_for("user_login"))
        else:
            flash("Email không tồn tại trong hệ thống.", "danger")
    return render_template("user/forgot_password.html")


@app.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    doctor = db.session.query(User).options(
        joinedload(User.doctor).joinedload(Doctor.doctor_departments).joinedload(DoctorDepartment.department),
        joinedload(User.doctor).joinedload(Doctor.medical_center)
    ).filter(User.id == doctor_id).first()

    if not doctor:
        flash('Không tìm thấy bác sĩ này.', 'danger')
        return redirect(url_for('home'))

    selected_date_str = request.args.get('appointment_date') or request.form.get('appointment_date')
    selected_date_obj = None
    if selected_date_str:
        try:
            selected_date_obj = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date_obj = None

    if request.method == 'POST':
        doctor_shift_id = request.form.get('doctor_shift_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birth_of_day_str = request.form.get('birth_of_day')
        gender = request.form.get('gender')

        if not all([doctor_shift_id, first_name, last_name, birth_of_day_str, gender]):
            flash('Vui lòng điền đầy đủ thông tin và chọn một khung giờ.', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=selected_date_str or ''))

        client_id = session.get('user_id')
        if not client_id:
            flash('Bạn cần đăng nhập để đặt lịch.', 'danger')
            return redirect(url_for('user_login'))

        doctor_shift = db.session.get(DoctorShift, doctor_shift_id)
        if not doctor_shift:
            flash('Khung giờ không hợp lệ.', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id))

        existing_ticket = db.session.query(Ticket).join(DoctorShift).filter(
            Ticket.client_id == client_id,
            DoctorShift.doctor_id == doctor_id,
            DoctorShift.work_date == doctor_shift.work_date,
            Ticket.status.in_([TicketStatus.PENDING, TicketStatus.CONFIRMED])
        ).first()

        if existing_ticket:
            flash(f'Bạn đã có lịch khám với bác sĩ này trong ngày {doctor_shift.work_date.strftime("%d/%m/%Y")}.',
                  'warning')
            return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=selected_date_str or ''))

        new_ticket = Ticket(
            uuid=str(uuid.uuid4()),
            doctor_shift_id=doctor_shift.id,
            client_id=client_id,
            status=TicketStatus.PENDING,
            first_name=first_name,
            last_name=last_name,
            birth_of_day=datetime.strptime(birth_of_day_str, '%Y-%m-%d').date(),
            gender=gender
        )
        db.session.add(new_ticket)
        db.session.commit()
        flash('Đặt lịch thành công! Vui lòng thanh toán.', 'success')
        return redirect(url_for('payment', ticket_uuid=new_ticket.uuid))

    # --- SỬA LỖI TRUY VẤN VÀ SẮP XẾP ---
    all_doctor_shifts = db.session.query(DoctorShift).join(Shift).outerjoin(Ticket).filter(
        DoctorShift.doctor_id == doctor_id,
        DoctorShift.work_date >= date.today(),
        DoctorShift.work_date <= date.today() + timedelta(days=7),
        Ticket.id == None  # <-- THÊM DÒNG NÀY: Chỉ lấy những ca chưa có vé (còn trống)
    ).order_by(DoctorShift.work_date, Shift.start_time).all()

    shifts_by_work_date = {}
    for ds in all_doctor_shifts:
        if ds.work_date not in shifts_by_work_date:
            shifts_by_work_date[ds.work_date] = []
        shifts_by_work_date[ds.work_date].append(ds)

    available_dates_for_template = []
    for work_date in sorted(shifts_by_work_date.keys()):
        available_dates_for_template.append({
            'date': work_date,
            'shift_count': len(shifts_by_work_date[work_date]),
            'is_selected': work_date == selected_date_obj
        })

    if not selected_date_obj and available_dates_for_template:
        first_available_date_str = available_dates_for_template[0]['date'].strftime('%Y-%m-%d')
        return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=first_available_date_str))

    current_date_shifts = {}
    if selected_date_obj and selected_date_obj in shifts_by_work_date:
        morning_shifts = [ds for ds in shifts_by_work_date[selected_date_obj] if ds.shift.start_time < time(12, 0)]
        afternoon_shifts = [ds for ds in shifts_by_work_date[selected_date_obj] if ds.shift.start_time >= time(12, 0)]
        if morning_shifts:
            current_date_shifts['Buổi Sáng'] = morning_shifts
        if afternoon_shifts:
            current_date_shifts['Buổi Chiều'] = afternoon_shifts

    current_user_info = g.user

    return render_template('doctor/book_appointment.html',
                           doctor=doctor,
                           available_dates=available_dates_for_template,
                           current_date_shifts=current_date_shifts,
                           selected_date=selected_date_str,
                           current_user_info=current_user_info)


@app.route('/payment/<string:ticket_uuid>')
def payment(ticket_uuid):
    ticket = db.session.query(Ticket).options(
        joinedload(Ticket.doctor_shift).joinedload(DoctorShift.doctor).joinedload(Doctor.user),
    ).filter(Ticket.uuid == ticket_uuid).first()
    if not ticket:
        flash('Không tìm thấy vé đặt lịch này.', 'danger')
        return redirect(url_for('home'))
    return render_template('payment/payment.html', ticket=ticket)


@app.route("/medical_center_details/<int:medical_center_id>")
def medical_center_details(medical_center_id):
    medical_center = db.session.get(MedicalCenter, medical_center_id)
    return render_template('hospital/medical_center_details.html', medical_center=medical_center)


@app.route('/doctor_details/<int:doctor_id>')
def doctor_details(doctor_id):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        flash('Không tìm thấy bác sĩ này.', 'danger')
        return redirect(url_for('home'))
    return render_template('doctor/doctor_details.html', doctor=doctor.user)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not g.user:
        flash('Vui lòng đăng nhập để xem thông tin cá nhân.', 'warning')
        return redirect(url_for('user_login'))

    user = g.user
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        birth_of_day_str = request.form.get('birth_of_day')
        if birth_of_day_str:
            user.birth_of_day = datetime.strptime(birth_of_day_str, '%Y-%m-%d').date()
        else:
            user.birth_of_day = None
        user.gender = request.form.get('gender')
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')

        try:
            db.session.commit()
            flash('Cập nhật thông tin cá nhân thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật thông tin: {e}', 'danger')
        return redirect(url_for('profile'))
    return render_template('user/profile.html', user=user)


if __name__ == '__main__':
    app.secret_key = 'your_secret_key'
    app.run(debug=True)