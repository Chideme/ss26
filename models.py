from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()


class Tank(db.Model):
    __tablename__="tanks"
    id = db.Column(db.Integer,primary_key=True)
    product = db.Column(db.String,nullable=False)

class Pump(db.Model):
    __tablename__="pumps"
    id = db.Column(db.Integer,primary_key =True,nullable=False)
    name= db.Column(db.String,nullable=False)
    tank_id = db.Column(db.Integer,db.ForeignKey("tanks.id"),nullable=False)

class PumpReading(db.Model):
    __tablename__ = "pump_readings"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    reading = db.Column(db.Integer, nullable=False)
    pump_id = db.Column(db.Integer, db.ForeignKey("pump.id"), nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    

class TankDip(db.Model):
    __tablename__ = "tank_dips"
    id = db.Column(db.Integer, primary_key=True)
    date= db.Column(db.Date, nullable=False)
    dip = db.Column(db.Integer,nullable=False)
    tank_id = db.Column(db.Integer, db.ForeignKey("tanks.id"), nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)



class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    username = db.Column(db.String,nullable=False)
    password = db.Column(db.String,nullable=False)
    role_id = db.Column(db.Integer,db.ForeignKey("roles.id"),nullable=False)


class Role(db.Model):
    __tablename__="roles"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name= db.Column(db.String,nullable=False)

class Customer(db.Model):
    __tablename__="customers"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name= db.Column(db.String,nullable=False)
    

class Shift(db.Model):
    __tablename__="shift"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date = db.Column(db.Date,nullable=False)
    daytime = db.Column(db.String,nullable=True)
    pump_readings = db.relationship("PumpReading", backref="shift",lazy=True)
    