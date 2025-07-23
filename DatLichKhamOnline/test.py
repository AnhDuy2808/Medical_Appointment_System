from DatLichKhamOnline import db, app
from models import User, MedicalCenter

if __name__ == "__main__":
    with app.app_context():
        print(User.query.filter_by(role="doctor").all())
        print(MedicalCenter.query.all())