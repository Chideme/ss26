import os
import urllib.request
from flask import redirect, render_template, request, session,flash,url_for
from functools import wraps
from models import *
from sqlalchemy import and_ , or_

def login_required(f):

    """

    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if session.get("user_id") is None:

            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):

    """

    Decorate routes to require Admin login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if session.get("user_id") != 1:
            flash("Access not allowed!!")
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function

def start_shift_first(f):

    """

    Decorate routes to check if start shift
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):
        shift_underway = Shift_Underway.query.get(1)
        if shift_underway.state == False:
            flash("Start shift first!!")
            return redirect(url_for('start_shift_update'))


        return f(*args, **kwargs)

    return decorated_function

def end_shift_first(f):

    """

    Decorate routes to end current shift is user attempts to starts a new shift
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):
        shift_underway = Shift_Underway.query.get(1)
        if shift_underway.state == True:
            flash("End shift first!!")
            return redirect(url_for('readings_entry'))


        return f(*args, **kwargs)

    return decorated_function

def sales_before_receipts(shift_id,product):
    products = Product.query.filter_by(name=str(product)).first()
    product_id = products.id
    invoices = Invoice.query.filter(and_(Invoice.shift_id == shift_id,Invoice.product == str(product))).all()
    total__invoices = sum([invoice.qty for invoice in invoices])
    price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = price.selling_price
    
    amount = total__invoices * price
    return amount

def product_sales(shift_id,product):
    product = Product.query.filter_by(name=str(product)).first()
    product_id = product.id
    tanks = Tank.query.filter_by(product_id=product_id).all()
    tanks = [i.id for i in tanks]
    prev_shift_id = int(shift_id)-1
    sales = 0
    
    pumps = Pump.query.filter(Pump.tank_id.in_(tanks)).all()
    for pump in pumps:
        prev_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev_shift_id,PumpReading.pump_id == pump.id)).first()
        prev_shift_reading = prev_shift_reading.litre_reading
        current_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == shift_id,PumpReading.pump_id == pump.id)).first()
        current_shift_reading = current_shift_reading.litre_reading
        sale = current_shift_reading - prev_shift_reading 
        sales += sale
    price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = price.selling_price
    amount = sales * price
    return amount

def receipt_product_qty(amount,shift_id,product):
    products = Product.query.filter_by(name=str(product)).first()
    product_id = products.id
    price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = price.selling_price
    product_available = product_sales(shift_id,product)-sales_before_receipts(shift_id,str(products)) #amount

    if product_available != 0 and product_available > 0:
        if product_available == amount or product_available > amount:
            product_qty = amount/price
        else:
            product_qty = product_available/price
    else:
        product_qty = 0
    
    return product_qty

def tank_2_productID(product):
    product = db.session.query(Tank,Product).filter(and_(Tank.product_id == Product.id,Tank.id == tank_id)).first()
    product = Product.query.filter_by(name=str(product[1])).first()
    product_id = product.id

    return product_id

def get_product_price(shift_id,product):
    product = Product.query.filter_by(name=product).first()
    product_id = product.id
    price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = price.selling_price
    return price

def total_customer_sales(results):
    d={}
    for customer in results:
        if customer[0] in d:
            d[customer[0]]= d[customer[0]] + (customer[1].price*customer[1].qty)
        else:
            if customer[0]=="Cash":
                pass
            else:
                d[customer[0]]= customer[1].price*customer[1].qty
    return d

