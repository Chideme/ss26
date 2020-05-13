""" Using this to test if  parts of the code are working or to manipulate the DB"""
from flask import Flask,render_template, request,jsonify
from models import *
from werkzeug.security import generate_password_hash
from random import randint
from sqlalchemy import and_ , or_
from helpers import *
from datetime import timedelta,datetime


DATABASE_URL= "postgres://localhost/ss26"  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():

        shift_id = 8
        prev = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
        s = Shift.query.order_by(Shift.id.desc()).offset(1).limit(1).first()
        #products = [(1,158),(2,69),(3,160),(4,0),(5,223),(6,8),(7,31),(8,3),(9,24),(10,13),(11,27),(12,7),(13,5)]
                
                

                
        print(prev.id)





   


if __name__=="__main__":
    with app.app_context():
        main()





