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
    tenant = "test"
    
    with db.session.connection(execution_options={"schema_translate_map":{"tenant":tenant}}):
        
        end_date = date.today()
        start_date = end_date - timedelta(days=100)
        accounts = Account.query.filter(Account.code.between(100,399)).all()
        report = {}
        for account in accounts:
            dr = Journal.query.filter(and_(account.id == Journal.dr,Journal.date.between(start_date,end_date))).all()
            cr = db.session.query(Account,Journal).filter(and_(account.id == Journal.cr,Journal.date.between(start_date,end_date))).all()
            print(account.account_name)
            print(dr)

with app.app_context():
        main()





