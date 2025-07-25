from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = "@%%@@^$!@$%%#@%%@PHAD%@$#$&*&"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:1234@localhost/mas?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app = app)

cloudinary.config(cloud_name='du6rdcpyi', api_key='943655164841773', api_secret='NlZzlTXX4fVHVswderpmViCM3oY')

if __name__ == '__main__':
    response = cloudinary.uploader.upload("image/bach_mai.jpg")
    print(response['secure_url'])