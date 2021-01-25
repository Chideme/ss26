import os
from flask import Flask,render_template, request
from models import *
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine,MetaData

#DATABASE_URL ="postgres://vyltpsivhqeaun:c0bb13175e810c1dcb143e03d1dc47b2ebaf46e095d9d6dfc8979d19f6a48e14@ec2-50-16-197-244.compute-1.amazonaws.com:5432/d3ud9s5a665gva"
#DATABASE_URL= "postgres://localhost/ss26"  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def main():

    #db.create_all()
     ## Insert management data
    password = generate_password_hash("Kud@94")
    op.bulk_insert(system_table,
    [
        {'name':'Admin','password':password}
    ],
     multiinsert=False)

    op.bulk_insert(package_table,
    [
        {'name':'free','number_of_days':7},
        {'name':'monthly','number_of_days':30},
        {'name':'yearly','number_of_days':365}
    ],
     multiinsert=False)

   

    op.bulk_insert(roles_table,
    [
        {'name':'admin'},
        {'name':'supervisor'},
        {'name':'view-only'}
    ],
     multiinsert=False)
    # 
if __name__=="__main__":
    with app.app_context():
        main()