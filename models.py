from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()


class Tank(db.Model):
    __tablename__="tanks"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String,nullable=False)
    product = db.Column(db.String,nullable=False)

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
    litre_reading = db.Column(db.Integer, nullable=False)
    money_reading = db.Column(db.Integer,nullable=True)
    pump_id = db.Column(db.Integer, db.ForeignKey("pumps.id"), nullable=False)
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

    def __repr__(self):
        username =self.username
        return "{}".format(username)


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
    

class Shift(db.Model):
    __tablename__="shift"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date = db.Column(db.Date,nullable=False)
    daytime = db.Column(db.String,nullable=True)

class Shift_Underway(db.Model):
    __tablename__="shift_underway"
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    state = db.Column(db.Boolean,nullable=False)


    