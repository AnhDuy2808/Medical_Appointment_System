import utils
from DatLichKhamOnline import app
from flask import render_template, request, flash, redirect, url_for, session
from models import User, MedicalCenter, DoctorDepartment, Department, DoctorMedicalCenter, Shift, Ticket, db, UserRole
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import joinedload # Import joinedload

@app.route("/")
def home():
    doctors = User.query.filter_by(role="doctor").all()
    medical_centers = MedicalCenter.query.all()
    return render_template('index.html', doctors=doctors, medical_centers=medical_centers)


@app.route("/search")
def search():
    query = request.args.get('q', '').lower()
    doctors = User.query.join(DoctorDepartment).join(Department).filter(
        User.role == "doctor",
        (User.first_name.ilike(f'%{query}%') | User.last_name.ilike(f'%{query}%') | Department.name.ilike(f'%{query}%'))
    ).distinct().all()
    medical_centers = MedicalCenter.query.filter(
        MedicalCenter.name.ilike(f'%{query}%') | MedicalCenter.description.ilike(f'%{query}%')
    ).all()
    print(f"Search query: {query}, Doctors found: {[d.first_name + ' ' + d.last_name for d in doctors]}, Medical Centers found: {[mc.name for mc in medical_centers]}")
    return render_template('index.html', doctors=doctors, medical_centers=medical_centers)


@app.route("/search_doctor")
def search_doctor():
    query = request.args.get('q', '').lower()
    doctors = User.query.join(DoctorDepartment).join(Department).filter(
        User.role == "doctor",
        (User.first_name.ilike(f'%{query}%') | User.last_name.ilike(f'%{query}%') | Department.name.ilike(f'%{query}%'))
    ).distinct().all()
    print(f"Found {len(doctors)} doctors: {[doctor.__str__() for doctor in doctors]}")
    return render_template('doctor/doctor_list.html', doctors=doctors)


@app.route("/search_medical_center")
def search_medical_center():
    query = request.args.get('q', '')
    medical_centers = MedicalCenter.query.filter(
        MedicalCenter.name.ilike(f'%{query}%') | MedicalCenter.description.ilike(f'%{query}%')
    ).all()
    return render_template('hospital/medical_center_list.html', medical_centers=medical_centers)


@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
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
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        avatar = request.form.get("avatar", "default_avatar.jpg")

        if User.query.filter_by(username=username).first():
            flash("Tên đăng nhập đã tồn tại.", "danger")
            return redirect(url_for("register"))

        new_user = User(first_name=first_name, last_name=last_name, username=username, password=password, email=email,
                        avatar=avatar, role=UserRole.USER.value) # Ensure role is value
        db.session.add(new_user)
        db.session.commit()
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("user_login"))

    return render_template("user/register.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Một liên kết đặt lại mật khẩu đã được gửi đến email của bạn.", "success")
            return redirect(url_for("user_login"))
        else:
            flash("Email không tồn tại trong hệ thống.", "danger")
    return render_template("user/forgot_password.html")


@app.route("/book_appointment/<int:doctor_id>", methods=["GET", "POST"])
def book_appointment(doctor_id):
    # Load doctor với các mối quan hệ specialties và work_places
    doctor = db.session.query(User).options(
        joinedload(User.specialties), # Eager load specialties
        joinedload(User.work_places) # Eager load work_places
    ).get_or_404(doctor_id)

    # Xử lý tham số ngày từ URL
    selected_date_str = request.args.get('appointment_date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today() # Mặc định nếu không hợp lệ
    else:
        selected_date = date.today() # Mặc định nếu không có ngày được chọn

    # Lấy các ca làm việc cho ngày đã chọn
    shifts = Shift.query.filter_by(doctor_id=doctor_id, work_date=selected_date).order_by(Shift.start_time).all()

    # Nhóm các ca làm việc theo buổi
    current_date_shifts = {
        'Buổi sáng': [],    # 00:00 - 12:00
        'Buổi chiều': [],   # 12:00 - 18:00
        'Buổi tối': []      # 18:00 - 24:00
    }

    for s in shifts:
        if s.start_time >= time(0, 0) and s.start_time < time(12, 0):
            current_date_shifts['Buổi sáng'].append(s)
        elif s.start_time >= time(12, 0) and s.start_time < time(18, 0):
            current_date_shifts['Buổi chiều'].append(s)
        else:
            current_date_shifts['Buổi tối'].append(s)
    current_date_shifts = {k: v for k, v in current_date_shifts.items() if v} # Loại bỏ các buổi không có ca nào

    # Tạo danh sách các ngày có lịch làm việc trong 7 ngày tới
    available_dates = []
    for i in range(7):
        d = date.today() + timedelta(days=i)
        shift_count = Shift.query.filter_by(doctor_id=doctor_id, work_date=d).count()
        available_dates.append({
            'date': d,
            'shift_count': shift_count,
            'is_selected': (d == selected_date)
        })

    if request.method == 'POST':
        ship_id = request.form.get('ship_id')
        if ship_id:
            ship = Shift.query.get_or_404(ship_id)
            client_id = session.get('user_id')
            if not client_id:
                flash("Vui lòng đăng nhập để đặt lịch.", "danger")
                return redirect(url_for("user_login"))

            new_ticket = Ticket(
                uuid=f"ticket-{doctor_id}-{ship.work_date}-{ship.start_time}",
                shifts_id=ship_id, # Use shifts_id to match model
                client_id=client_id,
                status="pending",
                first_name=User.query.get(client_id).first_name,
                last_name=User.query.get(client_id).last_name,
                birth_of_day=date(1990, 1, 1), # Dữ liệu mẫu
                gender="Male", # Dữ liệu mẫu
                appointment_time=ship.start_time
            )
            db.session.add(new_ticket)
            db.session.commit()
            flash("Đặt lịch thành công! Vui lòng thanh toán.", "success")
            return redirect(url_for("payment", ticket_id=new_ticket.id))
        else:
            flash("Vui lòng chọn một khung giờ.", "danger")
            return redirect(url_for("book_appointment", doctor_id=doctor_id, appointment_date=selected_date_str))

    return render_template('doctor/book_appointment.html',
                           doctor=doctor,
                           available_dates=available_dates,
                           current_date_shifts=current_date_shifts,
                           selected_date=selected_date.strftime('%Y-%m-%d') # Pass selected_date for input field
                          )

@app.route("/payment/<int:ticket_id>")
def payment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not session.get('user_id') or session.get('user_id') != ticket.client_id:
        flash("Bạn không có quyền truy cập trang này.", "danger")
        return redirect(url_for("home"))
    return render_template('payment/payment.html', ticket=ticket)


@app.route("/medical_center_details/<int:medical_center_id>")
def medical_center_details(medical_center_id):
    medical_center = MedicalCenter.query.get_or_404(medical_center_id)
    return render_template('hospital/medical_center_details.html', medical_center=medical_center)

@app.route("/doctor_details/<int:doctor_id>")
def doctor_details(doctor_id):
    # Sử dụng joinedload để tải trước thông tin
    # chuyên khoa và nơi công tác của bác sĩ
    doctor = db.session.query(User).options(
        joinedload(User.specialties),
        joinedload(User.work_places)
    ).get_or_404(doctor_id)
    return render_template('doctor/doctor_details.html', doctor=doctor)

if __name__ == '__main__':
    app.secret_key = 'your_secret_key'
    app.run(debug=True)