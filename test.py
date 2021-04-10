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
    tenant = "puma_service_station"
    customer_id=1
    with db.session.connection(execution_options={"schema_translate_map":{"tenant":tenant}}):
        
        report = db.session.query(CustomerTxn,Invoice,CustomerPayments,CreditNote).filter(Invoice.customer_id==customer_id,
                                        CustomerTxn.customer_id==customer_id,CustomerPayments.customer_id==customer_id,CreditNote.customer_id==customer_id,
                                       CustomerTxn.id==Invoice.customer_txn_id,CustomerTxn.id==CreditNote.customer_txn_id,CustomerTxn.id==CustomerPayments.customer_txn_id).order_by(CustomerTxn.date).order_by(CustomerTxn.id).all()

        print(report)
with app.app_context():
        main()





