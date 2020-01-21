""" Using this to test if  parts of the code are working or to manipulate the DB"""
from flask import Flask,render_template, request
from models import *
from werkzeug.security import generate_password_hash


DATABASE_URL= "postgres://localhost/ss26"  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    users = db.session.query(User,Role).filter(Role.id == User.role_id).all()
    #roles = Role.query.all()
    #db.drop_all()
    print(users)


if __name__=="__main__":
    with app.app_context():
        main()





