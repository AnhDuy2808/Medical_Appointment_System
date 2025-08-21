# DatLichKhamOnline/index.py
import uuid
from datetime import datetime, date, time

from flask import render_template, request, flash, redirect, url_for, session, \
    g  # Import g để lưu biến global cho request
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.sqltypes import Date

from DatLichKhamOnline import app, db  # Đảm bảo db được import
from models import User, MedicalCenter, DoctorDepartment, Department, Ticket, UserRole, Doctor, DoctorShift, \
    TicketStatus, Shift
from utils import str_to_datetime


# Middleware để tải thông tin người dùng trước mỗi request
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)  # Sử dụng db.session.get để lấy đối tượng User


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
    print(
        f"Search query: {query}, Doctors found: {[d.first_name + ' ' + d.last_name for d in doctors]}, Medical Centers found: {[mc.name for mc in medical_centers]}")
    return render_template('index.html', doctors=doctors, medical_centers=medical_centers)


@app.route("/search_doctor")
def search_doctor():
    query = request.args.get('q', '').lower()
    doctors = db.session.query(User).join(Doctor).join(DoctorDepartment).join(Department).filter(
        User.role == "doctor",
        (User.first_name.ilike(f'%{query}%') | User.last_name.ilike(f'%{query}%') | Department.name.ilike(f'%{query}%'))
    ).distinct().all()
    print(f"Found {len(doctors)} doctors: {[doctor.__str__() for doctor in doctors]}")
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

        if user and user.check_password(password):  # Sử dụng phương thức check_password
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
                        password=User.hash_password(raw_password),  # Băm mật khẩu bằng MD5
                        avatar=avatar, role=UserRole.USER.value)
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
                f"Một liên kết đặt lại mật khẩu đã được gửi đến email '{email}' của bạn (chức năng này chưa được triển khai đầy đủ).",
                "success")
            return redirect(url_for("user_login"))
        else:
            flash("Email không tồn tại trong hệ thống.", "danger")
    return render_template("user/forgot_password.html")


@app.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    # Lấy thông tin bác sĩ CÙNG VỚI CÁC THÔNG TIN CHUYÊN KHOA VÀ TRUNG TÂM Y TẾ CẦN THIẾT
    doctor = db.session.query(User).options(
        joinedload(User.doctor).joinedload(Doctor.doctor_departments).joinedload(DoctorDepartment.department),
        joinedload(User.doctor).joinedload(Doctor.medical_center)
    ).filter(User.id == doctor_id).first()

    if not doctor:
        flash('Không tìm thấy bác sĩ này.', 'danger')
        return redirect(url_for('home'))  # Chuyển hướng về trang chủ hoặc trang tìm bác sĩ

    # Lấy ngày đã chọn từ query string cho GET request (hoặc từ form nếu là POST)
    selected_date_str = request.args.get('appointment_date') or request.form.get('appointment_date')
    selected_date_obj = None
    if selected_date_str:
        try:
            selected_date_obj = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date_obj = None  # Xử lý ngày không hợp lệ

    if request.method == 'POST':
        # Đây là khi một khung giờ được chọn và submit dưới dạng form
        doctor_shift_id = request.form.get('doctor_shift_id')

        # Lấy thông tin bệnh nhân từ form
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birth_of_day_str = request.form.get('birth_of_day')
        gender = request.form.get('gender')

        print(
            f"first_name: {first_name}, last_name: {last_name}, birth_of_day_str: {birth_of_day_str}, gender: {gender}")

        # Kiểm tra dữ liệu bắt buộc
        if not doctor_shift_id:
            flash('Vui lòng chọn một khung giờ.', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=selected_date_str or ''))
        if not first_name or not last_name or not birth_of_day_str or not gender:
            flash('Vui lòng điền đầy đủ thông tin bệnh nhân.', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=selected_date_str or ''))

        doctor_shift = db.session.query(DoctorShift).filter_by(id=doctor_shift_id).options(
            joinedload(DoctorShift.shift)).first()
        if not doctor_shift:
            flash('Khung giờ không hợp lệ.', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=selected_date_str or ''))

        client_id = session.get('user_id')  # Hoặc g.user.id nếu bạn dùng Flask-Login và đảm bảo user đã đăng nhập
        if not client_id:
            flash('Bạn cần đăng nhập để đặt lịch.', 'danger')
            return redirect(url_for('user_login'))

        try:
            birth_of_day = datetime.strptime(birth_of_day_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Ngày sinh không hợp lệ.', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=selected_date_str or ''))

        # --- Bắt đầu kiểm tra "1 người 1 lịch khám trong ngày của bác sĩ" ---
        existing_ticket = db.session.query(Ticket).join(DoctorShift).filter(
            Ticket.client_id == client_id,
            DoctorShift.doctor_id == doctor_id,
            DoctorShift.work_date == DoctorShift.work_date,  # Kiểm tra trên cùng ngày làm việc
            Ticket.status.in_([TicketStatus.PENDING, TicketStatus.CONFIRMED])  # Trạng thái đang chờ hoặc đã xác nhận
        ).first()

        if existing_ticket:
            flash(
                f'Bạn đã có lịch khám với bác sĩ {doctor.first_name} {doctor.last_name} vào ngày {doctor_shift.work_date.strftime("%d/%m/%Y")} rồi.',
                'warning')
            return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=selected_date_str or ''))
        # --- Kết thúc kiểm tra ---

        # Tạo vé đặt lịch
        new_ticket_uuid = str(uuid.uuid4())
        new_ticket = Ticket(
            uuid=new_ticket_uuid,
            doctor_shift_id=doctor_shift.id,
            client_id=client_id,
            status=TicketStatus.PENDING,  # Trạng thái mặc định
            first_name=first_name,
            last_name=last_name,
            birth_of_day=birth_of_day,
            gender=gender,
        )
        db.session.add(new_ticket)
        db.session.commit()
        flash('Đặt lịch thành công! Vui lòng thanh toán.', 'success')
        return redirect(url_for('payment', ticket_uuid=new_ticket.uuid))

    # Logic cho GET request (hiển thị form đặt lịch)
    # Lấy tất cả các ca làm việc của bác sĩ trong tương lai
    all_doctor_shifts: list[DoctorShift] = db.session.query(DoctorShift).join(DoctorShift.shift).filter(
        DoctorShift.doctor_id == doctor_id,
        DoctorShift.work_date > date.today()
    ).order_by(DoctorShift.work_date).all()

    # Nhóm các ca làm việc theo ngày để hiển thị thanh chọn ngày
    shifts_by_work_date: dict[InstrumentedAttribute[Date], list[DoctorShift]] = {}
    for doctor_shift in all_doctor_shifts:
        if doctor_shift.work_date not in shifts_by_work_date:
            shifts_by_work_date[doctor_shift.work_date] = []
        shifts_by_work_date[doctor_shift.work_date].append(doctor_shift)

    # Chuẩn bị dữ liệu available_dates cho template
    available_dates_for_template = []
    for work_date in sorted(shifts_by_work_date.keys()):
        shift_count = len(shifts_by_work_date[work_date])
        is_selected = (work_date == selected_date_obj)  # Đánh dấu ngày được chọn
        available_dates_for_template.append({
            'date': work_date,
            'shift_count': shift_count,
            'is_selected': is_selected
        })

    # Nếu không có ngày nào được chọn hoặc ngày không hợp lệ, mặc định chọn ngày đầu tiên nếu có
    if not selected_date_obj and available_dates_for_template:
        first_available_date = available_dates_for_template[0]['date']
        first_available_date_str = first_available_date.strftime('%Y-%m-%d')
        # Redirect để cập nhật URL và hiển thị ca làm việc của ngày đầu tiên
        return redirect(url_for('book_appointment', doctor_id=doctor_id, appointment_date=first_available_date_str))

    # Lấy các ca làm việc cụ thể cho ngày đã chọn để hiển thị khung giờ
    current_date_shifts = {}
    if selected_date_obj and selected_date_obj in shifts_by_work_date:
        # Nhóm ca làm việc của ngày đã chọn thành sáng/chiều
        morning_shifts = []
        afternoon_shifts = []
        for doctor_shift in shifts_by_work_date[selected_date_obj]:
            if doctor_shift.shift.start_time < time(12, 0):  # Trước 12h là sáng
                morning_shifts.append(doctor_shift)
            else:  # Từ 12h trở đi là chiều
                afternoon_shifts.append(doctor_shift)

        if morning_shifts:
            current_date_shifts['Buổi Sáng'] = morning_shifts
        if afternoon_shifts:
            current_date_shifts['Buổi Chiều'] = afternoon_shifts

    # Lấy thông tin người dùng hiện tại để pre-fill form
    current_user_info = None
    if 'user_id' in session:  # Hoặc g.user nếu bạn dùng Flask-Login
        current_user_info = db.session.query(User).filter(User.id == session['user_id']).first()

    # Truyền dữ liệu cho template
    return render_template('doctor/book_appointment.html',
                           doctor=doctor,
                           available_dates=available_dates_for_template,
                           current_date_shifts=current_date_shifts,
                           selected_date=selected_date_str,  # Truyền lại ngày đã chọn để input type="date" giữ giá trị
                           current_user_info=current_user_info)


@app.route('/payment/<string:ticket_uuid>')
def payment(ticket_uuid):
    ticket = db.session.query(Ticket).options(
        joinedload(Ticket.doctor_shift).joinedload(DoctorShift.doctor).joinedload(Doctor.doctor_departments).joinedload(
            DoctorDepartment.department),
    ).filter(Ticket.uuid == ticket_uuid).first()

    if not ticket:
        flash('Không tìm thấy vé đặt lịch này.', 'danger')
        return redirect(url_for('home'))  # Hoặc một trang lỗi khác

    return render_template('payment/payment.html', ticket=ticket)


@app.route("/medical_center_details/<int:medical_center_id>")
def medical_center_details(medical_center_id):
    medical_center = db.session.query(MedicalCenter).filter(MedicalCenter.id == medical_center_id).first()
    return render_template('hospital/medical_center_details.html', medical_center=medical_center)


@app.route('/doctor_details/<int:doctor_id>')
def doctor_details(doctor_id):
    # Tải thông tin bác sĩ, bao gồm các khoa và trung tâm y tế liên quan
    doctor = db.session.query(Doctor).options(
        joinedload(Doctor.doctor_departments).joinedload(DoctorDepartment.department),
        joinedload(Doctor.medical_center),
        joinedload(Doctor.user)
    ).filter(Doctor.id == doctor_id).first()

    if not doctor:
        flash('Không tìm thấy bác sĩ này.', 'danger')
        return redirect(url_for('search_doctor'))  # Hoặc home nếu không có search_doctor

    # Lấy các ca làm việc của bác sĩ này trong tương lai
    shifts = db.session.query(DoctorShift).filter(
        DoctorShift.doctor_id == doctor_id,
        DoctorShift.work_date > date.today()
    ).options(joinedload(DoctorShift.shift)).order_by(DoctorShift.work_date).all()

    # Nhóm các ca làm việc theo ngày
    shifts_by_date = {}
    for shift in shifts:
        date_str = shift.work_date.strftime('%Y-%m-%d')
        if date_str not in shifts_by_date:
            shifts_by_date[date_str] = []
        shifts_by_date[date_str].append(shift)

    return render_template('doctor/doctor_details.html', doctor=doctor, shifts_by_date=shifts_by_date)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('Vui lòng đăng nhập để xem thông tin cá nhân.', 'warning')
        return redirect(url_for('user_login'))

    user = db.session.query(User).filter(User.id == user_id).first()
    if not user:
        flash('Không tìm thấy thông tin người dùng.', 'danger')
        # Xóa session nếu user không tồn tại trong DB
        session.pop('user_id', None)
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')

        birth_of_day_str = request.form.get('birth_of_day')
        if birth_of_day_str:
            try:
                user.birth_of_day = datetime.strptime(birth_of_day_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Ngày sinh không hợp lệ.', 'danger')
                return redirect(url_for('profile'))
        else:
            user.birth_of_day = None  # Cho phép xóa ngày sinh nếu trường trống

        user.gender = request.form.get('gender')
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')
        user.avatar = request.form.get('avatar')

        try:
            db.session.commit()
            flash('Cập nhật thông tin cá nhân thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật thông tin: {e}', 'danger')

        return redirect(url_for('profile'))

    return render_template('user/profile.html', user=user)


@app.route('/assign-shift', methods=['GET', 'POST'])
def assign_shift():
    user_id = session.get('user_id')
    date_query = request.args.get('date', None)
    selected_datetime = str_to_datetime(date_query)

    if not user_id:
        flash('Vui lòng đăng nhập để xem thông tin cá nhân.', 'warning')
        return redirect(url_for('user_login'))

    user = db.session.query(User).filter(User.id == user_id).first()
    if not user:
        flash('Không tìm thấy thông tin người dùng.', 'danger')
        # Xóa session nếu user không tồn tại trong DB
        session.pop('user_id', None)
        return redirect(url_for('user_login'))

    if user.role != UserRole.DOCTOR:
        flash('Bạn không có quyền truy cập vào trang này', 'danger')
        return redirect(url_for('home'))

    if request.method == 'GET':
        shifts = db.session.query(Shift).all()
        doctor_shifts = db.session.query(DoctorShift).join(Doctor).join(User).join(Shift).filter(
            DoctorShift.doctor_id == user.id,
            DoctorShift.work_date == selected_datetime.date()
        ).all()

        return render_template(
            'doctor/assign_shift.html',
            shifts=shifts,
            doctor_shifts=doctor_shifts,
            date=selected_datetime.date(),
        )

    if request.method == 'POST':
        date_query = request.form.get('date', None)
        selected_datetime = str_to_datetime(date_query)

        assign_ids_raw = request.form.get('assign_shift_ids', '')
        unassign_ids_raw = request.form.get('unassign_shift_ids', '')

        try:
            assign_ids = [int(x) for x in assign_ids_raw.split(',') if x.strip()]
            unassign_ids = [int(x) for x in unassign_ids_raw.split(',') if x.strip()]
        except ValueError:
            assign_ids, unassign_ids = [], []

        assigned_count = 0
        unassigned_count = 0
        blocked_unassign: list[int] = []

        for shift_id in assign_ids:
            shift = db.session.query(Shift).filter(Shift.id == shift_id).first()
            if not shift:
                continue
            exists = db.session.query(DoctorShift).filter(
                DoctorShift.doctor_id == user.id,
                DoctorShift.shift_id == shift_id,
                DoctorShift.work_date == selected_datetime.date()
            ).first()
            if not exists:
                new_ds = DoctorShift(
                    doctor_id=user.id,
                    shift_id=shift_id,
                    work_date=selected_datetime.date()
                )
                db.session.add(new_ds)
                assigned_count += 1

        for shift_id in unassign_ids:
            shift = db.session.query(Shift).filter(Shift.id == shift_id).first()
            if not shift:
                continue
            ds = db.session.query(DoctorShift).filter(
                DoctorShift.doctor_id == user.id,
                DoctorShift.shift_id == shift_id,
                DoctorShift.work_date == selected_datetime.date()
            ).first()
            if not ds:
                continue

            ticket = db.session.query(Ticket).filter(
                Ticket.doctor_shift_id == ds.id,
                Ticket.status.in_([TicketStatus.PENDING, TicketStatus.CONFIRMED])
            ).first()
            if ticket:
                blocked_unassign.append(shift_id)
                continue

            db.session.delete(ds)
            unassigned_count += 1

        try:
            db.session.commit()
            if assigned_count or unassigned_count:
                flash(f"Đã cập nhật: đăng ký {assigned_count} ca, hủy {unassigned_count} ca.", 'success')
            else:
                flash('Không có thay đổi nào được áp dụng.', 'info')

            if blocked_unassign:
                flash(
                    f"Không thể hủy các ca đã có vé đang chờ/xác nhận: {', '.join(map(str, blocked_unassign))}.",
                    'warning'
                )
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật ca làm việc: {e}', 'danger')

        return redirect(url_for('assign_shift', date=selected_datetime.date().strftime('%Y-%m-%d')))


if __name__ == '__main__':
    app.secret_key = 'your_secret_key'  # Rất quan trọng cho session
    app.run(debug=True)
