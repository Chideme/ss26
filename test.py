""" Using this to test if  parts of the code are working or to manipulate the DB"""
from flask import Flask,render_template, request
from models import *
from werkzeug.security import generate_password_hash
from random import randint
from sqlalchemy import and_, or_


DATABASE_URL= "postgres://localhost/ss26"  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    #users = db.session.query(Tank,Pump).filter(Tank.id == Pump.tank_id).all()
    #s = Shift.query.all()
    #shift = Shift.query.order_by(Shift.id.desc()).first()
    
    tank = Pump.query.filter_by(id=1).first()
    tank_id = tank.tank_id
    products = db.session.query(Tank,Product).filter(and_(Tank.product_id == Product.id,Tank.id == tank_id)).first()
    products = str(products[1])
    product = Product.query.filter_by(name=products).first()
    product_id = product.id
    #db.drop_all()
    print(product_id)
    
    


if __name__=="__main__":
    with app.app_context():
        main()





