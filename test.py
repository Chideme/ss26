""" Using this to test if  parts of the code are working or to manipulate the DB-The ultimate debugger"""
from flask import Flask,render_template, request,jsonify
from models import *
from werkzeug.security import generate_password_hash
from random import randint
from sqlalchemy import and_ , or_,create_engine,MetaData,Table,inspect
#from sqlalchemy_sqlschema import maintain_schema

from sqlalchemy.orm import Session
from helpers import *
from datetime import timedelta,datetime
from alembic_multischema import perSchema,getNonSystemSchemas


  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =  os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    with db.session.connection(execution_options={"schema_translate_map":{"tenant":'test10'}}):
        s = Supplier(name="kuda",contact_person="kuda",phone_number="1234")
        db.session.add(s)
        db.session.commit()

        
with app.app_context():
        main()





