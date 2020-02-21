from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()


class Tank(db.Model):
    __tablename__="tanks"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String,nullable=False)
    product_id = db.Column(db.Integer,db.ForeignKey("products.id"),nullable=False)

    def __repr__(self):
        name =self.name
        return "{}".format(name)


class Pump(db.Model):
    __tablename__="pumps"
    id = db.Column(db.Integer,primary_key =True,nullable=False)
    name= db.Column(db.String,nullable=False)
    tank_id = db.Column(db.Integer,db.ForeignKey("tanks.id"),nullable=False)

    def __repr__(self):
        
        name =self.name
        return "{}".format(name)
        
class PumpReading(db.Model):
    __tablename__ = "pump_readings"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    product_id = db.Column(db.Integer,db.ForeignKey("products.id"),nullable=False)
    litre_reading = db.Column(db.Float, nullable=False)
    money_reading = db.Column(db.Float,nullable=True)
    pump_id = db.Column(db.Integer, db.ForeignKey("pumps.id"), nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    

class TankDip(db.Model):
    __tablename__ = "tank_dips"
    id = db.Column(db.Integer, primary_key=True)
    date= db.Column(db.Date, nullable=False)
    dip = db.Column(db.Float,nullable=False)
    tank_id = db.Column(db.Integer, db.ForeignKey("tanks.id"), nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)



class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    username = db.Column(db.String,nullable=False)
    password = db.Column(db.String,nullable=False)
    role_id = db.Column(db.Integer,db.ForeignKey("roles.id"),nullable=False)

    def __repr__(self):
        username =self.username
        return "{}".format(username)

class Product(db.Model):
    __tablename__="products"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String,nullable=False)
    product_type=db.Column(db.String,nullable=False)
    price = db.Column(db.Float,nullable=False)
    tanks = db.relationship("Tank",backref="product",lazy=True)
    
    def __repr__(self):
        name =self.name
        return "{}".format(name)

class Role(db.Model):
    __tablename__="roles"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name= db.Column(db.String,nullable=False)
    users= db.relationship("User",backref="user",lazy=True)

    def __repr__(self):
        return "{}".format(self.name)

class Customer(db.Model):
    __tablename__="customers"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name= db.Column(db.String,nullable=False)
    contact_person =db.Column(db.String,nullable=True)
    phone_number = db.Column(db.String,nullable=True)

    def __repr__(self):
        return "{}".format(self.name)

    

class Shift(db.Model):
    __tablename__="shift"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date = db.Column(db.Date,nullable=False)
    daytime = db.Column(db.String,nullable=True)


    def __repr__(self):
        return "{}".format(self.id)
    

class Shift_Underway(db.Model):
    __tablename__="shift_underway"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    state = db.Column(db.Boolean,nullable=False)

class Fuel_Delivery(db.Model):
    __tablename__="fuel_delivery"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    tank_id = db.Column(db.Integer, db.ForeignKey("tanks.id"), nullable=False)
    date= db.Column(db.Date, nullable=False)
    qty = db.Column(db.Float,nullable=False)
    product_id = db.Column(db.Integer,db.ForeignKey("products.id"),nullable=True)
    document_number = db.Column(db.String,nullable=True)

class Invoice(db.Model):
    __tablename__="invoices"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    qty = db.Column(db.Float,nullable=False)
    product = db.Column(db.String,nullable=False)
    price= db.Column(db.Float,nullable=False)
    vehicle_number = db.Column(db.String,nullable=True)
    driver_name = db.Column(db.String,nullable=True)

class Account(db.Model):
    __tablename__="accounts"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    account_name= db.Column(db.String,nullable=False)
    account_category =db.Column(db.String,nullable=False)

    def __repr__(self):

        return "{}".format(self.account_name)

class SaleReceipt(db.Model):
    __tablename__="sales_receipts"
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    account_id= db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    amount= db.Column(db.Integer,nullable=False)
   

class PayOut(db.Model):
    __tablename__="payouts"
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    amount= db.Column(db.Integer,nullable=False)
    source_account= db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    pay_out_account = db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)


class CashUp(db.Model):
    __tablename__="cash_up"
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    account_id= db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    expected_amount= db.Column(db.Integer,nullable=False)
    actual_amount= db.Column(db.Integer,nullable=False)
    expected_amount= db.Column(db.Integer,nullable=False)
    variance = db.Column(db.Integer,nullable=False)

class Price(db.Model):
    __tablename__="prices"
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    product_id= db.Column(db.Integer,db.ForeignKey("products.id"),nullable=False)
    price= db.Column(db.Float,nullable=False)
    




    