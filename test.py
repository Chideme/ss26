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
    
    with db.session.connection(execution_options={"schema_translate_map":{"tenant":tenant}}):
        
        invoices = Invoice.query.all()
        payments = CustomerPayments.query.all()
        credit_notes = CreditNote.query.all()
       
        for invoice in invoices:
            amount= round(invoice.price*invoice.qty,2)
            date = invoice.date
            post_balance=customer_txn_opening_balance(date,invoice.customer_id) + amount
            txn = CustomerTxn(date=invoice.date,txn_type="Invoice",customer_id=invoice.customer_id,amount=amount,post_balance=post_balance)
            db.session.add(txn)
            db.session.flush()
            invoice.customer_txn_id = txn.id
            update_customer_balances(date,amount,invoice.customer_id,txn.txn_type)
        for invoice in credit_notes:
            date = invoice.date
            amount= round(invoice.selling_price*invoice.qty,2)
            post_balance=customer_txn_opening_balance(date,invoice.customer_id) - amount
            txn = CustomerTxn(date=invoice.date,txn_type="Credit Note",customer_id=invoice.customer_id,amount=amount,post_balance=post_balance)
            db.session.add(txn)
            db.session.flush()
            invoice.customer_txn_id = txn.id
            update_customer_balances(date,amount,invoice.customer_id,txn.txn_type)
        
        for paymemt in payments:
            date = payment.date
            amount= payment.amount
            post_balance=customer_txn_opening_balance(date,payment.customer_id) - amount
            txn = CustomerTxn(date=payment.date,txn_type="Payment",customer_id=payment.customer_id,amount=amount,post_balance=post_balance)
            db.session.add(txn)
            db.session.flush()
            invoice.customer_txn_id = txn.id
            update_customer_balances(date,amount,invoice.customer_id,txn.txn_type)
       
        db.session.commit()
with app.app_context():
        main()





