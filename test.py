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
    
    with db.session.connection(execution_options={"schema_translate_map":{"tenant":'test2'}}):

        start_date = "2019-01-01"
        end_date = "2020-02-10"
        #start_date = datetime.strptime(start_date,"%Y-%m-%d")
        #end_date = datetime.strptime(end_date,"%Y-%m-%d")
                
        data = fuel_mnth_sales(start_date,end_date)
        
        print(data)
        data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
        print(data)
        sorted_date= sorted_dates([i for i in data])
        data_info = [data[i] for i in sorted_date]
        data_dates = [i.strftime('%b-%y')  for i in sorted_date]
        report = jsonify({'Date':data_dates,'Data':data_info})
        print(report)     

        
    #db.drop_all()


    
   

if __name__=="__main__":
    with app.app_context():
        main()





