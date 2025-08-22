# DatLichKhamOnline/index.py
import uuid
from datetime import datetime, date, time, timedelta

from flask import render_template, request, flash, redirect, url_for, session, \
    g  # Import g để lưu biến global cho request
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.sqltypes import Date
from flask import jsonify
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


@app.context_processor
def inject_current_year():
    """Làm cho biến 'current_year' có sẵn trong tất cả các template."""
    return {'current_year': datetime.now().year}


@app.route("/")
def home():
    # Cập nhật truy vấn để tải đầy đủ thông tin liên quan của bác sĩ
    doctors = db.session.query(User).options(
        subqueryload(User.doctor).options(
            joinedload(Doctor.medical_center),
            joinedload(Doctor.doctor_departments).joinedload(DoctorDepartment.department)
        )
    ).filter(User.role == UserRole.DOCTOR).limit(6).all()  # Lấy 6 bác sĩ nổi bật

    # Lấy 6 trung tâm y tế nổi bật
    medical_centers = db.session.query(MedicalCenter).limit(6).all()

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

    # --- CẬP NHẬT TRUY VẤN ĐỂ TẢI ĐẦY ĐỦ DỮ LIỆU ---
    doctors_query = db.session.query(User).options(
        # Tải đối tượng Doctor liên quan và các thuộc tính của nó
        subqueryload(User.doctor).options(
            joinedload(Doctor.medical_center),  # Tải thông tin bệnh viện (nơi công tác)
            joinedload(Doctor.doctor_departments).joinedload(DoctorDepartment.department)  # Tải chuyên khoa
        )
    ).join(User.doctor).filter(User.role == UserRole.DOCTOR)  # Luôn join vào Doctor

    # Thêm điều kiện tìm kiếm nếu có
    if query:
        doctors_query = doctors_query.join(Doctor.doctor_departments).join(Department).filter(
            (User.first_name.ilike(f'%{query}%')) |
            (User.last_name.ilike(f'%{query}%')) |
            (Department.name.ilike(f'%{query}%'))
        ).distinct()

    doctors = doctors_query.all()

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
            flash(f"Đăng nhập thành công! Chào mừng {user.first_name} {user.last_name}.", "success")

            # --- PHÂN LUỒNG THEO VAI TRÒ ---
            if user.role == UserRole.DOCTOR:
                return redirect(url_for('doctor_dashboard'))
            # Mở rộng cho các vai trò khác nếu cần, ví dụ:
            # elif user.role == UserRole.ADMIN:
            #     return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for("home"))
            # --- KẾT THÚC PHÂN LUỒNG ---
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")

    return render_template("user/login.html")


@app.route('/doctor/dashboard', methods=['GET', 'POST'])
def doctor_dashboard():
    # Bảo vệ route: Chỉ bác sĩ mới được truy cập
    if not g.user or g.user.role != UserRole.DOCTOR:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('home'))

    # Xử lý khi bác sĩ nộp form đăng ký lịch mới
    if request.method == 'POST':
        work_date_str = request.form.get('work_date')
        selected_shift_ids = request.form.getlist('shift_ids')

        if not work_date_str or not selected_shift_ids:
            flash('Vui lòng chọn ngày và ít nhất một ca làm việc.', 'warning')
        else:
            work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
            new_shifts_count = 0
            for shift_id in selected_shift_ids:
                existing_shift = db.session.query(DoctorShift).filter_by(
                    doctor_id=g.user.id,
                    shift_id=int(shift_id),
                    work_date=work_date
                ).first()

                if not existing_shift:
                    new_doctor_shift = DoctorShift(
                        doctor_id=g.user.id,
                        shift_id=int(shift_id),
                        work_date=work_date
                    )
                    db.session.add(new_doctor_shift)
                    new_shifts_count += 1

            if new_shifts_count > 0:
                db.session.commit()
                flash(
                    f'Đã đăng ký thành công {new_shifts_count} ca làm việc mới cho ngày {work_date.strftime("%d/%m/%Y")}.',
                    'success')
            else:
                flash('Các ca bạn chọn đã được đăng ký từ trước.', 'info')

        return redirect(url_for('doctor_dashboard'))

    # Lấy dữ liệu để hiển thị cho trang (GET request)
    all_shifts = db.session.query(Shift).order_by(Shift.start_time).all()

    registered_shifts = db.session.query(DoctorShift).join(Shift).filter(
        DoctorShift.doctor_id == g.user.id,
        DoctorShift.work_date >= date.today()
    ).order_by(DoctorShift.work_date, Shift.start_time).all()

    shifts_by_date = {}
    for shift in registered_shifts:
        work_date = shift.work_date
        if work_date not in shifts_by_date:
            shifts_by_date[work_date] = []
        shifts_by_date[work_date].append(shift)

    # **SỬA LỖI Ở ĐÂY: Lấy ngày hôm nay và truyền vào template**
    today_date = date.today()

    return render_template('doctor/dashboard.html',
                           all_shifts=all_shifts,
                           shifts_by_date=shifts_by_date,
                           today_date=today_date)  # <-- Truyền biến mới


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
    # --- CẬP NHẬT TRUY VẤN ĐỂ TẢI ĐẦY ĐỦ DỮ LIỆU ---
    # Truy vấn User và tải trước tất cả các thông tin liên quan cần thiết
    doctor_user = db.session.query(User).options(
        subqueryload(User.doctor).options(
            joinedload(Doctor.medical_center),
            joinedload(Doctor.doctor_departments).joinedload(DoctorDepartment.department)
        )
    ).filter(User.id == doctor_id, User.role == UserRole.DOCTOR).first_or_404()

    # first_or_404() sẽ tự động trả về trang lỗi 404 nếu không tìm thấy bác sĩ

    return render_template('doctor/doctor_details.html', doctor=doctor_user)


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


@app.route('/select_payment_method/<string:ticket_uuid>')
def select_payment_method(ticket_uuid):
    ticket = db.session.query(Ticket).filter_by(uuid=ticket_uuid).first_or_404()
    return render_template('payment/select_payment_method.html', ticket=ticket)


@app.route('/pay/<string:method>/<string:ticket_uuid>')
def initiate_payment(method, ticket_uuid):
    ticket = db.session.query(Ticket).filter_by(uuid=ticket_uuid).first_or_404()

    # Kiểm tra vé đã thanh toán chưa
    if ticket.status == TicketStatus.CONFIRMED:
        flash('Lịch hẹn này đã được thanh toán rồi.', 'info')
        return redirect(url_for('payment_return', ticket_uuid=ticket.uuid))

    # --- LOGIC TÍCH HỢP API THẬT SỰ SẼ NẰM Ở ĐÂY ---
    # 1. Chuẩn bị các tham số: amount, orderId, orderInfo, returnUrl, ipnUrl,...
    # 2. Tạo chữ ký (signature) bằng Secret Key
    # 3. Gọi API của MoMo hoặc VNPay để lấy payUrl

    # Giả lập: In ra thông tin và chuyển hướng thẳng đến trang kết quả
    print(f"Bắt đầu quá trình thanh toán cho vé {ticket.uuid} bằng {method.upper()}")
    print("Trong thực tế, tại đây sẽ gọi API và chuyển hướng đến payUrl của cổng thanh toán.")

    # Giả lập thành công: Chuyển hướng người dùng đến trang kết quả
    # Trong thực tế, đây sẽ là `return redirect(payUrl)`
    flash('Đang chuyển hướng đến cổng thanh toán...', 'info')
    return redirect(url_for('payment_return', ticket_uuid=ticket.uuid, success='true'))


@app.route('/payment/return')
def payment_return():
    ticket_uuid = request.args.get('ticket_uuid')
    ticket = db.session.query(Ticket).filter_by(uuid=ticket_uuid).first_or_404()

    # Trong thực tế, bạn sẽ kiểm tra các tham số trả về từ MoMo/VNPay và xác thực chữ ký
    # Tuy nhiên, nguồn đáng tin cậy nhất là trạng thái trong DB (được cập nhật bởi IPN)

    # Giả lập cập nhật trạng thái thành công (bình thường việc này do IPN làm)
    is_success = request.args.get('success') == 'true'
    if is_success and ticket.status != TicketStatus.CONFIRMED:
        ticket.status = TicketStatus.CONFIRMED
        db.session.commit()
        print(f"GIẢ LẬP: Cập nhật trạng thái vé {ticket.uuid} thành CONFIRMED.")

    return render_template('payment/payment_result.html', ticket=ticket)


# Route 3: Nơi MoMo/VNPay gọi để thông báo kết quả (Server-to-Server)
@app.route('/payment/ipn', methods=['POST'])
def payment_ipn():
    # Đây là endpoint cực kỳ quan trọng, xử lý ngầm
    data = request.get_json()
    print("Đã nhận được IPN:", data)

    # --- LOGIC XỬ LÝ IPN THẬT SỰ ---
    # 1. Lấy dữ liệu từ request của cổng thanh toán
    # 2. Kiểm tra chữ ký (signature) để đảm bảo dữ liệu là hợp lệ và từ cổng thanh toán gửi đến
    # 3. Lấy thông tin đơn hàng (vé) từ database dựa trên orderId (hoặc uuid) trong dữ liệu IPN
    # 4. Kiểm tra số tiền (amount) xem có khớp không
    # 5. Cập nhật trạng thái vé trong database (ví dụ: PENDING -> CONFIRMED)
    # 6. Phản hồi lại cho server của cổng thanh toán theo đúng định dạng họ yêu cầu

    # Giả lập:
    # resultCode = data.get('resultCode')
    # if resultCode == 0:
    #     ticket_uuid = data.get('orderId')
    #     ticket = db.session.query(Ticket).filter_by(uuid=ticket_uuid).first()
    #     if ticket:
    #         ticket.status = TicketStatus.CONFIRMED
    #         db.session.commit()
    #         print(f"IPN: Cập nhật vé {ticket_uuid} thành công.")

    # Phải trả về response cho MoMo/VNPay, nếu không họ sẽ gửi lại IPN nhiều lần
    return jsonify({'message': 'IPN received'}), 200


@app.route('/appointment_history')
def appointment_history():
    # Check if the user is logged in
    if not g.user:
        flash('Vui lòng đăng nhập để xem lịch sử đặt khám.', 'warning')
        return redirect(url_for('user_login'))

    # Query all tickets for the current user
    # **FIX:** Added a second .join(Shift) to make the 'shifts.start_time' column available for sorting.
    tickets = db.session.query(Ticket).options(
        joinedload(Ticket.doctor_shift).joinedload(DoctorShift.shift),
        joinedload(Ticket.doctor_shift).joinedload(DoctorShift.doctor).joinedload(Doctor.user),
        joinedload(Ticket.doctor_shift).joinedload(DoctorShift.doctor).joinedload(Doctor.medical_center),
        joinedload(Ticket.doctor_shift).joinedload(DoctorShift.doctor).joinedload(Doctor.doctor_departments).joinedload(
            DoctorDepartment.department)
    ).filter(
        Ticket.client_id == g.user.id
    ).join(
        DoctorShift, Ticket.doctor_shift_id == DoctorShift.id
    ).join(
        Shift, DoctorShift.shift_id == Shift.id
    ).order_by(
        DoctorShift.work_date.desc(), Shift.start_time.desc()
    ).all()

    return render_template('user/appointment_history.html', tickets=tickets)


@app.route('/doctor/edit_shift/<string:work_date>', methods=['GET', 'POST'])
def edit_doctor_shift(work_date):
    if not g.user or g.user.role != UserRole.DOCTOR:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('home'))

    try:
        work_date_obj = datetime.strptime(work_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Ngày không hợp lệ.', 'danger')
        return redirect(url_for('doctor_dashboard'))

    if request.method == 'POST':
        # Lấy danh sách ID các ca được chọn từ form
        selected_shift_ids = {int(id) for id in request.form.getlist('shift_ids')}

        # Lấy danh sách ID các ca đã đăng ký trước đó trong ngày
        existing_shifts = db.session.query(DoctorShift).filter_by(doctor_id=g.user.id, work_date=work_date_obj).all()
        existing_shift_ids = {ds.shift_id for ds in existing_shifts}

        # Ca cần thêm mới = ca được chọn NHƯNG chưa có trong DB
        shifts_to_add = selected_shift_ids - existing_shift_ids
        # Ca cần xóa = ca đã có trong DB NHƯNG không được chọn nữa
        shifts_to_delete = existing_shift_ids - selected_shift_ids

        # Thêm ca mới
        for shift_id in shifts_to_add:
            # Kiểm tra xem ca này đã có người đặt chưa (an toàn)
            has_ticket = db.session.query(Ticket).join(DoctorShift).filter(
                DoctorShift.doctor_id == g.user.id,
                DoctorShift.work_date == work_date_obj,
                DoctorShift.shift_id == shift_id
            ).first()
            if not has_ticket:
                db.session.add(DoctorShift(doctor_id=g.user.id, shift_id=shift_id, work_date=work_date_obj))

        # Xóa ca cũ
        for shift_id in shifts_to_delete:
            shift_to_remove = next((ds for ds in existing_shifts if ds.shift_id == shift_id), None)
            # Chỉ xóa nếu ca đó chưa có người đặt
            if shift_to_remove and not shift_to_remove.ticket:
                db.session.delete(shift_to_remove)

        db.session.commit()
        flash(f'Cập nhật lịch làm việc cho ngày {work_date_obj.strftime("%d/%m/%Y")} thành công!', 'success')
        return redirect(url_for('doctor_dashboard'))

    # Logic cho GET request
    all_shifts = db.session.query(Shift).order_by(Shift.start_time).all()
    registered_shifts_for_date = db.session.query(DoctorShift).filter_by(doctor_id=g.user.id,
                                                                         work_date=work_date_obj).all()
    registered_shift_ids = {ds.shift_id for ds in registered_shifts_for_date}

    return render_template('doctor/edit_shift.html',
                           work_date=work_date_obj,
                           all_shifts=all_shifts,
                           registered_shift_ids=registered_shift_ids)


@app.route('/doctor/delete_shifts_by_date/<string:work_date>', methods=['POST'])
def delete_doctor_shifts_by_date(work_date):
    if not g.user or g.user.role != UserRole.DOCTOR:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('home'))

    try:
        work_date_obj = datetime.strptime(work_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Ngày không hợp lệ.', 'danger')
        return redirect(url_for('doctor_dashboard'))

    # Lấy tất cả ca làm việc trong ngày của bác sĩ
    shifts_to_delete = db.session.query(DoctorShift).filter_by(
        doctor_id=g.user.id,
        work_date=work_date_obj
    ).all()

    deleted_count = 0
    for shift in shifts_to_delete:
        # An toàn: chỉ xóa những ca chưa có người đặt
        if not shift.ticket:
            db.session.delete(shift)
            deleted_count += 1

    db.session.commit()

    if deleted_count > 0:
        flash(f'Đã xóa thành công {deleted_count} ca làm việc trong ngày {work_date_obj.strftime("%d/%m/%Y")}.',
              'success')
    else:
        flash(f'Không thể xóa vì tất cả các ca trong ngày {work_date_obj.strftime("%d/%m/%Y")} đã có bệnh nhân đặt.',
              'warning')

    return redirect(url_for('doctor_dashboard'))


@app.route('/doctor/appointments')
def doctor_appointments():
    # Bảo vệ route, chỉ bác sĩ mới được vào
    if not g.user or g.user.role != UserRole.DOCTOR:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('home'))

    # Lấy ngày được chọn từ query parameter để lọc (nếu có)
    selected_date_str = request.args.get('filter_date')
    query_date = None
    if selected_date_str:
        try:
            query_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Định dạng ngày không hợp lệ.', 'warning')

    # Xây dựng câu truy vấn cơ bản
    query = db.session.query(Ticket).join(DoctorShift).filter(
        DoctorShift.doctor_id == g.user.id
    )

    # Thêm điều kiện lọc theo ngày nếu có
    if query_date:
        query = query.filter(DoctorShift.work_date == query_date)

    # Sắp xếp lịch hẹn theo ngày và giờ bắt đầu
    appointments = query.join(Shift).order_by(
        DoctorShift.work_date.desc(),
        Shift.start_time.asc()
    ).all()

    return render_template('doctor/appointments.html',
                           appointments=appointments,
                           filter_date=selected_date_str)


@app.route('/doctor/profile', methods=['GET', 'POST'])
def doctor_profile():
    # Bảo vệ route, chỉ bác sĩ mới được vào
    if not g.user or g.user.role != UserRole.DOCTOR:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('home'))

    # Lấy thông tin bác sĩ từ thông tin người dùng
    doctor_info = g.user.doctor

    if request.method == 'POST':
        # Cập nhật thông tin chung trong model User
        g.user.first_name = request.form.get('first_name')
        g.user.last_name = request.form.get('last_name')
        g.user.phone = request.form.get('phone')
        g.user.address = request.form.get('address')

        # Cập nhật thông tin chuyên môn trong model Doctor
        if doctor_info:
            doctor_info.description = request.form.get('description')
            doctor_info.medical_center_id = request.form.get('medical_center_id')
            doctor_info.start_year = request.form.get('start_year', type=int)

        try:
            db.session.commit()
            flash('Cập nhật hồ sơ thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật hồ sơ: {e}', 'danger')

        return redirect(url_for('doctor_profile'))

    # Lấy danh sách các trung tâm y tế để hiển thị trong dropdown
    medical_centers = db.session.query(MedicalCenter).all()

    return render_template('doctor/profile.html', user=g.user, doctor=doctor_info, medical_centers=medical_centers)


if __name__ == '__main__':
    app.secret_key = 'your_secret_key'
    app.run(debug=True)
