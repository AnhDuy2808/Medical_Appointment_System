import utils
from DatLichKhamOnline import app
from flask import render_template, request, flash, redirect, url_for, session
from models import User, MedicalCenter, DoctorDepartment, DoctorMedicalCenter, Ship, Ticket, db
from datetime import datetime


@app.route("/")
def home():
    doctors = User.query.filter_by(role="doctor").all()
    medical_centers = MedicalCenter.query.all()
    return render_template('index.html', doctors=doctors, medical_centers=medical_centers)


@app.route("/search")
def search():
    query = request.args.get('q', '').lower()
    doctors = User.query.filter_by(role="doctor").filter(
        User.first_name.ilike(f'%{query}%') | User.last_name.ilike(f'%{query}%')
    ).all()
    medical_centers = MedicalCenter.query.filter(
        MedicalCenter.name.ilike(f'%{query}%') | MedicalCenter.description.ilike(f'%{query}%')
    ).all()
    return render_template('index.html', doctors=doctors, medical_centers=medical_centers)


@app.route("/search_doctor")
def search_doctor():
    query = request.args.get('q', '')
    doctors = User.query.filter_by(role="doctor").filter(
        User.first_name.ilike(f'%{query}%') | User.last_name.ilike(f'%{query}%')
    ).all()
    print(f"Found {len(doctors)} doctors: {[doctor.__str__() for doctor in doctors]}")  # Debug output
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
        role = request.form.get("role", "user")

        if User.query.filter_by(username=username).first():
            flash("Tên đăng nhập đã tồn tại.", "danger")
            return redirect(url_for("register"))

        new_user = User(first_name=first_name, last_name=last_name, username=username, password=password, email=email,
                        avatar=avatar, role=role)
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
    doctor = User.query.get_or_404(doctor_id)
    ships = Ship.query.filter_by(doctor_id=doctor_id, work_date=datetime.utcnow().date()).all()
    if not ships:
        flash("Không có lịch làm việc nào cho bác sĩ vào hôm nay.", "warning")
    if request.method == "POST":
        ship_id = request.form["ship_id"]
        ship = Ship.query.get_or_404(ship_id)
        client_id = session.get('user_id')
        if not client_id:
            flash("Vui lòng đăng nhập để đặt lịch.", "danger")
            return redirect(url_for("user_login"))

        new_ticket = Ticket(
            uuid=f"ticket-{doctor_id}-{ship.work_date}-{ship.start_time}",
            ship_id=ship_id,
            client_id=client_id,
            status="pending",
            first_name=User.query.get(client_id).first_name,
            last_name=User.query.get(client_id).last_name,
            birth_of_day="1990-01-01",
            gender="Male",
            appointment_time=ship.start_time
        )
        db.session.add(new_ticket)
        db.session.commit()
        flash("Đặt lịch thành công! Vui lòng thanh toán.", "success")
        return redirect(url_for("payment", ticket_id=new_ticket.id))
    return render_template('doctor/book_appointment.html', doctor=doctor, ships=ships)


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


if __name__ == '__main__':
    app.secret_key = 'your_secret_key'
    app.run(debug=True)