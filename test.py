""" Using this to test if  parts of the code are working or to manipulate the DB"""
from flask import Flask,render_template, request
from models import *
from werkzeug.security import generate_password_hash
from random import randint
from sqlalchemy import and_ , or_
from helpers import *


DATABASE_URL= "postgres://localhost/ss26"  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    #users = db.session.query(Tank,Pump).filter(Tank.id == Pump.tank_id).all()
    #s = Shift.query.all()
    shift = Shift.query.order_by(Shift.id.desc()).first()
    shift_id = shift.id
    tank_id = 1
    #db.drop_all()
    product_sales = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == shift_id)).all()
    petrol_sales = [sum([i[1].litre_reading for i in product_sales if i[0].name =="Petrol" ]),db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.name=="Petrol")).all()]
    #customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id)).all()
    #r = total_customer_sales(customer_sales)
    #expenses = db.session.query(PayOut,Account).filter(and_(PayOut.pay_out_account== Account.id,PayOut.shift_id==shift_id)).all()
    print(shift.id)
    print("------")
    print(shift.daytime)
        
    
   



if __name__=="__main__":
    with app.app_context():
        main()





