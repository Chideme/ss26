""" Using this to test if  parts of the code are working or to manipulate the DB-The ultimate debugger"""
from flask import Flask,render_template, request,jsonify
from models import *
from werkzeug.security import generate_password_hash
from random import randint
from sqlalchemy import and_ , or_,create_engine,MetaData,Table,inspect
#from sqlalchemy_sqlschema import maintain_schema
from flask_mail import Mail, Message

from sqlalchemy.orm import Session
from helpers import *
from datetime import timedelta,datetime
from alembic_multischema import perSchema,getNonSystemSchemas


  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =  os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'kudaysystems@gmail.com',
    MAIL_PASSWORD = 'kuda2020',
))
mail = Mail(app)
def main():
    tenant = "marvel"

    with db.session.connection(execution_options={"schema_translate_map":{"tenant":tenant}}):
        #pump_readings[pump.name]=[prev_shift_reading,current_shift_reading]
        attend_sale = db.session.query(AttendantSale,User).filter(AttendantSale.shift_id==shift_id,AttendantSale.attendant_id==User.id).all()
                            
        pump_attendant = {i[0].pump_id: i[1] for i in attend_sale}
        pump_readings= get_pump_readings(shift_id,prev_shift_id)
        

        print(report)
with app.app_context():
        main()





