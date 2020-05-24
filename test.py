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


DATABASE_URL= "postgres://localhost/ss26"  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    
    #with db.session.connection(execution_options={"schema_translate_map":{"tenant":'test4'}}):
    engine= create_engine(DATABASE_URL)
    meta = MetaData()
    meta.reflect(bind=engine,resolve_fks=True,schema='tenant')
    with engine.connect().execution_options(schema_translate_map={"tenant":'test5','public':'public'}) as conn:
        meta.create_all(bind=conn,checkfirst=True)
    #db.drop_all()
if __name__=="__main__":
    with app.app_context():
        main()





