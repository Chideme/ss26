import os
import urllib.request
import random
import string

from flask import redirect, render_template, request, session,flash,url_for
from flask_login import current_user
from functools import wraps
from models import *
from collections import *
from sqlalchemy import and_ , or_,MetaData,create_engine
from decimal import Decimal,getcontext

from datetime import timedelta


##########

DATABASE_URL=os.getenv("DATABASE_URL")
getcontext().prec = 2
####################




def login_required(f):

    """

    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if session.get("user_id") is None:

            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function

def system_admin_required(f):

    """

    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if session.get("system_admin") is None:

            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function

def check_schema(f):

   
    """
    Decorate routes to require users to be in the correct schema
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    

    @wraps(f)

    def decorated_function(*args, **kwargs):
        
            

        if session['user_tenant'] != session['tenant']:
            flash("Not Authorised to view company data")
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function




    
        

def admin_required(f):

    """

    Decorate routes to require Admin login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if session.get("role_id") != 1:
            flash("Access not allowed, Log in as the Admin !!")
            return redirect(url_for('dashboard',heading='Sales'))

        return f(*args, **kwargs)

    return decorated_function


def view_only(f):

    """

    Decorate routes to require Admin login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if session.get("role_id") == 3:
            flash("You can only view data !!")
            return redirect(url_for('dashboard',heading='Sales'))

        return f(*args, **kwargs)

    return decorated_function

def start_shift_first(f):

    """

    Decorate routes to check if a shift has started
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):
        if session["shift_underway"] == False:
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
        
        if session["shift_underway"] == True:
            flash("End shift first!!")
            return redirect(url_for('ss26'))


        return f(*args, **kwargs)

    return decorated_function




def sales_before_receipts(shift_id,product_id):
    products = Product.query.get(product_id)
    product_id = products.id
    invoices = Invoice.query.filter(and_(Invoice.shift_id == shift_id,Invoice.product_id == product_id)).all()
    total__invoices = sum([invoice.qty for invoice in invoices])
    price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = products.selling_price
    
    amount = total__invoices * price
    return amount

def product_sales(shift_id,product_id):
    product = Product.query.get(product_id)
    product_id = product.id
    tanks = Tank.query.filter_by(product_id=product_id).all()
    tanks = [i.id for i in tanks]
    prev = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
    prev_shift_id = prev.id
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
    price = product.selling_price
    amount = sales * price
    return amount

def receipt_product_qty(amount,shift_id,product_id):
    product_id = product_id
    product = Product.query.get(product_id)
    #price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = product.selling_price
    product_available = product_sales(shift_id,product_id)-sales_before_receipts(shift_id,product_id) #amount

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

def get_product_price(shift_id,product_id):
    product = Product.query.filter_by(id=product_id).first()
    product_id = product.id
    price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = product.selling_price
    return price

def total_customer_sales(results):
    d={}
    for customer in results:
        if customer[0] in d:
            d[customer[0]]= d[customer[0]] + (customer[1].price*customer[1].qty)
        else:
            
            d[customer[0]]= customer[1].price*customer[1].qty
    return d


def sorted_dates(dates):
    ordinals = [i.toordinal() for i in dates]
    sort_ordinals = sorted(ordinals)
    sorted_dates = [date.fromordinal(i) for i in sort_ordinals]

    
    return sorted_dates

def check_first_date(date):
    shifts= Shift.query.order_by(Shift.id.asc()).all()
    check_shift = Shift.query.filter_by(date=date).first()
    if check_shift == None:
        if shifts:
            return shifts[1].date
            
        else:
            return date
    else:
        return date

def product_sales_litres(shift_id,prev_shift_id):
    """ Calculates Sales per fuel product e.g Total Petrol Sales per shift"""
    products = Product.query.filter_by(product_type="Fuels").all()
    prices = db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.name=="Petrol")).all()
    prev_readings = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == prev_shift_id)).all()
    curr_readings = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == shift_id)).all()
    product_sales = {}
    for product in products:
        prev_prod_readings = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == prev_shift_id,Product.id==product.id)).first()
        if prev_prod_readings:
            current_product_reading = sum([i[1].litre_reading for i in curr_readings if i[0].id == product.id])
            previous_product_reading = sum([i[1].litre_reading for i in prev_readings if i[0].id == product.id])
            sales = current_product_reading-previous_product_reading
            prices = db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.id==product.id)).first()
            if prices:
                product_sales[product.name] = (sales,prices)
            else:
                product_sales[product.name] = (sales,product)
                
    return product_sales


def lube_sales(shift_id,prev_shift_id):
    """Calcuates lube sales per shift"""
    products = Product.query.filter_by(product_type="Lubricants").all()
    product_sales = {}

    for product in products:
            prev = LubeQty.query.filter(and_(LubeQty.shift_id == prev_shift_id,LubeQty.product_id== product.id)).first()
            curr = LubeQty.query.filter(and_(LubeQty.shift_id == shift_id,LubeQty.product_id== product.id)).first()
            if prev and curr: # check if previous shift exists
                delivery = Delivery.query.filter(and_(Delivery.shift_id==shift_id,Delivery.product_id==product.id)).all()
                deliveries = sum([i.qty for i in delivery])
                sales = ( prev.qty + deliveries)-curr.qty
                cost_price = product.cost_price
                selling_price = product.selling_price
                mls = product.unit
                
                #remove spaces fron names so as to render modals correctly
                #modal_name = product.name.replace(" ","")
                product_sales[product.name]= (prev.qty,curr.qty,sales,cost_price,selling_price,mls,deliveries)
            else:
                pass

    return product_sales

def lubes_daily_profit_report(start_date,end_date):
    """ Lubes day-to-day profit"""
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    profit = {}
    for shift in shifts:
        shift_id = shift.id
        prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
        if prev_shift:
            prev_shift_id = prev_shift.id
            product_sales = lube_sales(shift_id,prev_shift_id)
            sales = sum([product_sales[i][0]*product_sales[i][4] for i in product_sales])
            cost = sum([product_sales[i][0]*product_sales[i][3] for i in product_sales])
            
            if shift.date in profit:
                profit[shift.date] = profit[shift.date] + (sales - cost)
            else:
                profit[shift.date]= sales - cost

    return profit

def lubes_mnth_profit_report(start_date,end_date):
    """fuel month to month profit"""
    days = lubes_daily_profit_report(start_date,end_date)
    report = {}
    for day in days:
        month = day.strftime('%b-%y')
        if month in report:
            report[month] += days[day]
        else:
            report[month] = days[day]
    return report

def fuel_daily_profit_report(start_date,end_date):
    """ fuel day-to-day profit"""
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    profit = {}
    for shift in shifts:
        shift_id = shift.id
        prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
        if prev_shift:
            prev_shift_id = prev_shift.id
            litres = product_sales_litres(shift_id,prev_shift_id)
            sales = sum([litres[i][0]*litres[i][1][1].selling_price for i in litres])
            cost = sum([litres[i][0]*litres[i][1][1].cost_price for i in litres])
            
            if shift.date in profit:
                profit[shift.date] = profit[shift.date] + (sales - cost)
            else:
                profit[shift.date]= sales - cost

    return profit




def fuel_mnth_profit_report(start_date,end_date):
    """fuel month to month profit"""
    days = fuel_daily_profit_report(start_date,end_date)
    report = {}
    for day in days:
        month = day.strftime('%b-%y')
        if month in report:
            report[month] += days[day]
        else:
            report[month] = days[day]
    return report

def fuel_product_profit_statement(start_date,end_date):
    """Profit per product """
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    profit = {}
    for shift in shifts:
        shift_id = shift.id
        prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
        if prev_shift:
            prev_shift_id = prev_shift.id
            product = product_sales_litres(shift_id,prev_shift_id)
            if shift.date in profit:
                for prod in product:
                    profit[shift.date][prod][0] = profit[shift.date][prod][0]+ product[prod][0]
            else:
                profit[shift.date] ={i:[product[i][0],product[i][1][1].selling_price,product[i][1][1].cost_price,product[i][1][1].selling_price-product[i][1][1].cost_price] for i in product}
            

    return profit
   


def get_tank_variance(start_date,end_date,tank_id):
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    tank_dips={}
    cumulative = 0
    cumulativeP = 0
    cumulative_tank_sales = 0
    cumulative_pump_sales = 0
    for shift in shifts:
        prev = Shift.query.filter(Shift.id < shift.id).order_by(Shift.id.desc()).first()
        if prev:
            prev_shift_id = prev.id
            curr_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==shift.id,Tank.id==tank_id)).all()
            prev_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==prev_shift_id,Tank.id==tank_id)).all()
            prev_shift_dip = TankDip.query.filter(and_(TankDip.shift_id ==prev_shift_id,TankDip.tank_id == tank_id)).first()
            #exclude starting shift (shift 1)
            if prev_pump_reading and prev_shift_dip:
                pump_sales = sum([i[2].litre_reading for i in curr_pump_reading])-sum([i[2].litre_reading for i in prev_pump_reading])
                prev_shift_dip = TankDip.query.filter(and_(TankDip.shift_id ==prev_shift_id,TankDip.tank_id == tank_id)).first()
                prev_shift_dip = prev_shift_dip.dip
                current_shift_dip= TankDip.query.filter(and_(TankDip.shift_id == shift.id,TankDip.tank_id == tank_id)).first()
                current_shift_dip = current_shift_dip.dip
                delivery = Delivery.query.filter(and_(Delivery.shift_id==shift.id,Delivery.tank_id==tank_id)).all()
                deliveries = sum([i.qty for i in delivery])
                tank_sales = float(prev_shift_dip+deliveries-current_shift_dip)
                shrinkage2sales = float(pump_sales-tank_sales)
                cumulative = cumulative + shrinkage2sales
                cumulative_tank_sales = cumulative_tank_sales + tank_sales
                cumulative_pump_sales =cumulative_pump_sales+ pump_sales
                try:
                    cumulativeP = cumulative/cumulative_tank_sales *100
                except ZeroDivisionError:
                    cumulativeP = 0
                tank_dips[shift.id]=[shift.date,prev_shift_dip,current_shift_dip,deliveries,tank_sales,cumulative_tank_sales,pump_sales,shrinkage2sales,cumulative,cumulativeP,cumulative_pump_sales]

    return tank_dips

def daily_sales_summary(tanks,start_date,end_date):
    sales_summary= {}

    for tank in tanks:
    
        tank_dips = get_tank_variance(start_date,end_date,tank.id) # get details per tank per shift
        for shift in tank_dips:
            # aggregate to get data per day and all tanks
            if  tank_dips[shift][0] in sales_summary:
                n = len(sales_summary[tank_dips[shift][0]])
                for i in range(n):
                    sales_summary[tank_dips[shift][0]][i]+=tank_dips[shift][i+1]
            else:
                sales_summary[tank_dips[shift][0]]= [0.0]*10    
                for i in range(10):
                    
                    sales_summary[tank_dips[shift][0]][i] = tank_dips[shift][i+1]
        
    return sales_summary 

    
    
def tank_variance_daily_report(start_date,end_date,tank_id):
    """Tank Variance report for dashboard"""
    report = {}
    v = get_tank_variance(start_date,end_date,tank_id)
    for shift in v:
        if v[shift][0] in report:
            report[v[shift][0]][0] += v[shift][9]
        else:
            report[v[shift][0]] =v[shift][9]
   
    return report


def cash_sales(amount,customer_id,shift_id,date):
    """ Calculates invoices as per amount, as cash sales usually lack product information"""
    amount =  amount
    products = Product.query.filter_by(product_type="Fuels").all()
    products_qty={}
    for product in products:
        product_qty = receipt_product_qty(amount,shift_id,product.id)
        if product_qty >1:
            products_qty[product.name]=float(product_qty)
        else:
            pass
    
    for prod in products_qty:
        while products_qty[prod] > 1 and amount:
            product = Product.query.filter_by(name=prod).first()
            sales_price = get_product_price(shift_id,product.id)
            if products_qty[prod]*sales_price < amount:
                qty = products_qty[prod]
                invoice = Invoice(date=date,product_id=product.id,shift_id=shift_id,customer_id=customer_id,qty=qty,price=sales_price)
                db.session.add(invoice)
                db.session.flush()
                inv_amt = float(products_qty[prod] * sales_price)
                amount = float(amount-inv_amt)
                products_qty[prod] = int(products_qty[prod]-qty)
            elif products_qty[prod]*sales_price > amount or products_qty[prod]*sales_price == amount :
                qty = float(amount/sales_price)
                invoice = Invoice(date=date,product_id=product.id,shift_id=shift_id,customer_id=customer_id,qty=qty,price=sales_price)
                db.session.add(invoice)
                inv_amt = float(qty * sales_price)
                amount = float(amount-inv_amt)
                products_qty[prod] = int(products_qty[prod]-qty)
                
        
            elif products_qty[prod] < 1:
                break

    

    return True



def get_month_day1(end_date):
    """fuel month to date  sales"""
    today = end_date
    month =today.month
    year = today.year
    first_day = date(year,month,1)
    return first_day


def fuel_daily_sales(start_date,end_date):
    """fuel day to day  sales"""
    
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).order_by(Shift.id.desc()).all()
    daily_sales = {}
    
    for shift in shifts:
        shift_id = shift.id
        prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
        if prev_shift:
            prev_shift_id = prev_shift.id
            product_sales = product_sales_litres(shift_id,prev_shift_id)
            total = sum([product_sales[i][0] for i in product_sales])
            
            if shift.date in daily_sales:
                daily_sales[shift.date]+=total
            else:
                daily_sales[shift.date]=total

    return daily_sales
    
def daily_sales_analysis(start_date,end_date):
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).order_by(Shift.id.desc()).all()
    daily_sales = {}
    
    for shift in shifts:
        shift_id = shift.id
        prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
        if prev_shift:
            customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id)).all()
            prev_shift_id = prev_shift.id
            product_sales = product_sales_litres(shift_id,prev_shift_id)
            total = sum([product_sales[i][0] for i in product_sales])
            expected_deposits= sum([product_sales[i][0]*product_sales[i][1][1].selling_price for i in product_sales])
            sales_per_customer = total_customer_sales(customer_sales)
            actual_deposits = sum([sales_per_customer[i] for i in sales_per_customer])
            if shift.date in daily_sales:
                daily_sales[shift.date][0]+=total
                daily_sales[shift.date][1]+=expected_deposits
                daily_sales[shift.date][2]+=actual_deposits
                
            else:
                daily_sales[shift.date]=total,expected_deposits,actual_deposits

    return daily_sales

def fuel_mnth_sales(start_date,end_date):
    """fuel month to month sales"""
    days = fuel_daily_sales(start_date,end_date)
    report = {}
    for day in days:
        month = day.strftime('%b-%y')
        if month in report:
            report[month] += days[day]
        else:
            report[month] = days[day]
    return report

def lubes_mnth_sales(start_date,end_date):
    """lubes month to month sales"""
    days = lubes_daily_sales(start_date,end_date)
    report = {}
    for day in days:
        month = day.strftime('%b-%y')
        if month in report:
            report[month] += days[day]
        else:
            report[month] = days[day]
    return report



def fuel_sales_avg(start_date,end_date):
    """fuel  average for the current"""
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    daily_sales = fuel_daily_sales(start_date,end_date)
    total = sum([daily_sales[i] for i in daily_sales ])
    start_date,end_date = shifts[0].date,shifts[-1].date
    days= (end_date - start_date).days  + 1
    try:
        avg = total/days
    except ZeroDivisionError:
        avg = total

    return avg

def lubes_daily_sales(start_date,end_date):
    """Lubes  sales between particular dates"""

    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    daily_sales ={}
    for shift in shifts:
        shift_id = shift.id
        prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
        if prev_shift:
            prev_shift_id = prev_shift.id
            product_sales = lube_sales(shift_id,prev_shift_id)
            total = sum([product_sales[i][2]*product_sales[i][5] for i in product_sales])/1000
            
            if shift.date in daily_sales:
                daily_sales[shift.date]+=total
            else:
                daily_sales[shift.date]=total

        

    return daily_sales
    

def lubes_sales_avg(start_date,end_date):
    """Lubes average for the current dates"""
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    if shifts:
        daily_sales = lubes_daily_sales(start_date,end_date)
        total = sum([daily_sales[i] for i in daily_sales ])
        end_date= shifts[-1].date
        start_date= shifts[0].date
        days= (end_date - start_date).days + 1
        try:    
            avg = total/days
        except ZeroDivisionError:
            avg = total

        return avg
    else:
        return False


def get_pump_readings(shift_id,prev_shift_id):
    """Query for the driveway report ss26 """
    pump_readings = {}
    pumps = Pump.query.all()
    for pump in pumps:
        prev_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev_shift_id,PumpReading.pump_id == pump.id)).first()
        current_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == shift_id,PumpReading.pump_id == pump.id)).first()
        if prev_shift_reading:
            if current_shift_reading:
                prev_shift_reading = prev_shift_reading.litre_reading,prev_shift_reading.money_reading
                current_shift_reading = current_shift_reading.litre_reading,current_shift_reading.money_reading
                pump_readings[pump.name]=[prev_shift_reading,current_shift_reading]
        else:
            if current_shift_reading:
                current_shift_reading = current_shift_reading.litre_reading,current_shift_reading.money_reading
                prev_shift_reading = pump_readings[pump.name].litre_reading,pump_readings[pump.name].money_reading
                pump_readings[pump.name]=[prev_shift_reading,current_shift_reading]
    return pump_readings


def pump_meter_reading(pump_id,start_date,end_date):
    """Query for pump readings per day """
    pump = Pump.query.get(pump_id)
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    dates = [shift.date for shift in shifts]
    dates = sorted_dates(dates)
    pump_readings = {}
    if shifts:
        for date in dates:
            current_shift= Shift.query.filter_by(date=date).order_by(Shift.id.desc()).first()
            shift_id = current_shift.id
            prev_date = current_shift.date -timedelta(days=1)
            prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
            if prev_shift:
                prev_shift_id = prev_shift.id
            else:
                prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                prev_shift_id = prev_shift.id if prev_shift else shift_id
            prev_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev_shift_id,PumpReading.pump_id == pump.id)).first()
            current_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == shift_id,PumpReading.pump_id == pump.id)).first()
            if prev_shift_reading:
                if current_shift_reading:
                    prev_shift_reading = prev_shift_reading.litre_reading,prev_shift_reading.money_reading
                    current_shift_reading = current_shift_reading.litre_reading,current_shift_reading.money_reading
                    pump_readings[date]=[prev_shift_reading[0],current_shift_reading[0]]
            else:
                if current_shift_reading:
                    current_shift_reading = current_shift_reading.litre_reading,current_shift_reading.money_reading
                    prev_shift_reading = pump_readings[pump.name].litre_reading,pump_readings[pump.name].money_reading
                    pump_readings[date]= [prev_shift_reading[0],current_shift_reading[0]]
    return pump_readings



def get_tank_dips(shift_id,prev_shift_id):
    tank_dips = {}
    tanks = Tank.query.all()
    for tank in tanks:
        prev_shift_dip = TankDip.query.filter(and_(TankDip.shift_id ==prev_shift_id,TankDip.tank_id == tank.id)).first()
        current_shift_dip= TankDip.query.filter(and_(TankDip.shift_id == shift_id,TankDip.tank_id == tank.id)).first()
        
        curr_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==shift_id,Tank.id==tank.id)).all()
        prev_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==prev_shift_id,Tank.id==tank.id)).all()
        if curr_pump_reading and prev_pump_reading:
            try:
                pump_sales = sum([i[2].litre_reading for i in curr_pump_reading])-sum([i[2].litre_reading for i in prev_pump_reading])
            except:
                pump_sales = 0
        if prev_shift_dip and current_shift_dip:
            prev_shift_dip = prev_shift_dip.dip
            current_shift_dip = current_shift_dip.dip
            delivery = Delivery.query.filter(and_(Delivery.shift_id==shift_id,Delivery.tank_id==tank.id)).all()
            deliveries = sum([i.qty for i in delivery]) if delivery else 0
            tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales,deliveries,tank.id]
    return tank_dips


def get_driveway_data(shift_id,prev_shift_id):
    current_shift = Shift.query.get(shift_id)
    data = {}
    data['pump_readings'] = get_pump_readings(shift_id,prev_shift_id)
    data['pumps'] = Pump.query.order_by(Pump.id.asc()).all()
    data['tank_dips'] = get_tank_dips(shift_id,prev_shift_id)
    data['tanks'] = Tank.query.order_by(Tank.id.asc()).all()
    data['suppliers'] = Supplier.query.all()
    product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
    data['product_sales_ltr'] = product_sales_ltr
    data['cash_account'] = Customer.query.filter_by(name="Cash").first()
    customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Customer.name != "Cash")).all()
    sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer)
    data['total_sales_ltr']= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
    data['total_sales_amt']= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1][1].selling_price for product in product_sales_ltr])
    cash_sales = customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Customer.name == "Cash")).all()
    cash_breakdown = total_customer_sales(cash_sales)
    receivable = Account.query.filter_by(account_name="Accounts Receivables").first()
    data['cash_customers'] = Customer.query.filter(Customer.account_id != receivable.id).all()
    #sales_breakdown["Cash"] = data['total_sales_amt']- sum([sales_breakdown[i] for i in sales_breakdown])
    sales_breakdown["Cash"] = sum([cash_breakdown[i] for i in cash_breakdown])
    data['sales_breakdown'] = sales_breakdown
    data['sales_breakdom_amt'] =  sum([sales_breakdown[i] for i in sales_breakdown])
    expenses = db.session.query(PayOut,Account).filter(and_(PayOut.pay_out_account== Account.id,PayOut.shift_id==shift_id)).all()
    data['expenses'] = expenses
    data['total_cash_expenses'] = sum([i[0].amount for i in expenses])
    data['cash_up'] = CashUp.query.filter_by(shift_id=shift_id).first()
    data['products'] = Product.query.filter_by(product_type="Fuels").order_by(Product.id.asc()).all()
    data['coupons'] = Coupon.query.all()
    data['customers'] = Customer.query.all()
    #data['cash_customers'] = Customer.query.filter_by(account_type="Cash").all()
    data['expense_accounts'] = Account.query.filter_by(account_category="Expense").all()
    data['cash_accounts'] = Account.query.filter_by(account_category="Cash").all()
    ######## query report data
    data['accounts'] = Account.query.all()
    data['end_date'] = current_shift.date
    end_date= current_shift.date
    data['avg_sales'] = fuel_sales_avg(get_month_day1(end_date),end_date)
    daily_sales = fuel_daily_sales(get_month_day1(end_date),end_date) 
    data['mnth_sales'] = sum([daily_sales[i] for i in daily_sales])
    lubes_daily_sale = lubes_daily_sales(get_month_day1(end_date),end_date)
    data['lubes_daily_sale']= lubes_daily_sale
    lubes_mnth_sales = sum([lubes_daily_sale[i] for i in lubes_daily_sale])
    data['lubes_mnth_sales'] = sum([lubes_daily_sale[i] for i in lubes_daily_sale])
    data['lube_avg'] = lubes_sales_avg(get_month_day1(end_date),end_date)
    total_lubes_shift_sales = lube_sales(shift_id,prev_shift_id)
    data['total_lubes_shift_sales']=sum([total_lubes_shift_sales[i][5]*total_lubes_shift_sales[i][2] for i in total_lubes_shift_sales])/1000


    return data
    

def create_tenant_tables(schema):
    engine= create_engine(DATABASE_URL)
    meta = MetaData()
    meta.reflect(bind=engine,resolve_fks=True,schema='tenant')
    with engine.connect().execution_options(schema_translate_map={"tenant":schema,'public':'public'}) as conn:
        meta.create_all(bind=conn,checkfirst=True)
    
    return True

def create_schema_name(company_name):
    n =company_name.lower()
    ln = n.split(' ')
    if len(ln)>1:
        schema = n.replace(' ','_')
    else:
        schema = n
    tenants = Tenant.query.all()
    
    return schema

def create_dict(pumps):
    """Creates a dict out of a pump query list to generate variable names"""
    pump_dict ={}
    for pump in pumps:
        pump_dict[pump.name] = pump
    return pump_dict

def get_random_string():
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(8))
    return result_str

def customer_statement(customer_id,start_date,end_date):
    """Returns Customer statement"""
  
    total_invoices = Invoice.query.filter(and_(Invoice.customer_id==customer_id,Invoice.date < start_date)).all()
    total_payments = CustomerPayments.query.filter(and_(CustomerPayments.customer_id==customer_id,CustomerPayments.date < start_date)).all()
    customer = Customer.query.get(customer_id)
    invoices = db.session.query(Invoice,Product).filter(and_(Invoice.product_id == Product.id,Invoice.customer_id==customer_id,Invoice.date.between(start_date,end_date))).all()
    payments = CustomerPayments.query.filter(and_(CustomerPayments.customer_id==customer_id,CustomerPayments.date.between(start_date,end_date))).all()     
    balance = sum([i.qty * i.price for i in total_invoices]) - sum([i.amount for i in total_payments])
    balance = balance + customer.opening_balance
    report = {"balance":balance}
    for invoice in invoices:
        details = "Driver: {}, Vehicle Reg: {}, Product: {}, Qty: {}, Price: {}".format(invoice[0].driver_name,invoice[0].vehicle_number,invoice[1].name,invoice[0].qty,invoice[0].price)
        amount = invoice[0].qty*invoice[0].price
        amount = round(amount,2)
        report[invoice[0].id] = {"date":invoice[0].date,"details":details,"dr":amount,"cr":0}
    for payment in payments:
        amount = float(payment.amount)
        amount = round(amount,2)
        details  = "Top up - {}".format(payment.ref)
       
        report[payment.id] = {"date":payment.date,"details":details,"dr":0,"cr":amount}
        
def supplier_statement(supplier_id,start_date,end_date):
    """Returns Supplier statement"""
  
    total_deliveries = Delivery.query.filter(and_(Delivery.supplier==supplier_id,Delivery.date < start_date)).all()
    total_payments = SupplierPayments.query.filter(and_(SupplierPayments.supplier_id==supplier_id,SupplierPayments.date < start_date)).all()
    supplier = Supplier.query.get(supplier_id)
    deliveries = db.session.query(Delivery,Product).filter(and_(Delivery.product_id == Product.id,Delivery.supplier==supplier_id,Delivery.date.between(start_date,end_date))).all()
    payments = SupplierPayments.query.filter(and_(SupplierPayments.supplier_id==supplier_id,SupplierPayments.date.between(start_date,end_date))).all()     
    balance = sum([i.qty * i.cost_price for i in total_deliveries]) - sum([i.amount for i in total_payments])
    balance = balance + supplier.opening_balance
    report = {"balance":balance}
    for delivery in deliveries:
        details = str(delivery[0].document_number)
        amount = delivery[0].qty*delivery[0].cost_price
        amount = round(amount,2)
        report[delivery[0].id] = {"date":delivery[0].date,"details":details,"dr":0,"cr":amount}
    for payment in payments:
        amount = float(payment.amount)
        amount = round(amount,2)
        details  = "Top up - {}".format(payment.ref)
       
        report[payment.id] = {"date":payment.date,"details":details,"dr":amount,"cr":0}       
    return report
def fuel_variance_amt(shift_id):
    """ Calculate Variance Amount for journal posting """
    shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
    prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
    tanks = get_tank_dips(shift_id,prev_shift.id)
    sales = 0.00
    variance = 0.00
    for tank in tanks:
        i = db.session.query(Product,Tank).filter(Product.id ==Tank.product_id,Tank.id==int(tanks[tank][4])).first()
        avg_price = i[0].avg_price
        sale = (tanks[tank][0]+tanks[tank][3])-tanks[tank][1]
        sales += sale*avg_price
        variance += (tanks[tank][2]-sale)*avg_price
# tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales,deliveries,tank.id]
    return sales,variance

def post_fuel_variance_journals(shift_id):
    """Post amount for fuel shrinkages to journals """
    amount = fuel_variance_amt(shift_id)
    shift = Shift.query.get(shift_id)
    variance_acc = Account.query.filter_by(account_name="Fuel Shrinkages").first()
    inventory = Account.query.filter_by(account_name="Fuel Inventory").first()
    cogs = Account.query.filter_by(account_name="Fuel COGS").first()
    detail_variance = "Shift {} variance".format(shift_id)
    detail_cogs = "Shift {} cost of goods sold".format(shift_id)
    if amount[1]:
        variance_journal = Journal(date=shift.date,details=detail_variance,amount=amount[1],dr=variance_acc.id,cr=inventory.id,created_by=session['user_id'])
        db.session.add(variance_journal)
    if amount[0]:
        cogs_journal =Journal(date=shift.date,details=detail_cogs,amount=amount[0],dr=cogs.id,cr=inventory.id,created_by=session['user_id'])
        db.session.add(cogs_journal)
        db.session.flush()
    return True
    
def coupon_amount(shift_id,coupon_id):
    """ Calculate amount for Coupon Receivables posting """
    coupon_sales = db.session.query(Coupon,CouponSale,Product).filter(and_(Coupon.id==CouponSale.coupon_id,CouponSale.shift_id==shift_id,CouponSale.product_id==Product.id,CouponSale.coupon_id==coupon_id)).all()
    amount = sum([(i[0].coupon_qty* i[1].qty * i[2].selling_price )for i in coupon_sales ])
    return amount

def cash_sales_amount(shift_id):
    """ Sales receipts total sales/shift for journal posting """
    receipts = SaleReceipt.query.filter_by(shift_id=shift_id).all()
    amount = sum([i.amount for i in receipts])
    return amount


def post_fuel_sales_journals(shift_id):
    """ Post non cash amount to debtor control account """
    shift = Shift.query.get(shift_id)
    invoices = Invoice.query.filter_by(shift_id=shift_id)
    total_receivable_amount = sum([i.price*i.qty for i in invoices])
    coupon_sales_amt = coupon_amount(shift_id)
    cash_sales_amt = cash_sales_amount(shift_id)
    sales_acc = Account.query.filter_by(account_name="Fuel Sales").first()
    debtor = Account.query.filter_by(account_name="Accounts Receivables").first()
    details = "Shift {} sales".format(shift_id)
    coupon_sales_amt = coupon_amount(shift_id)
    non_cash_receivable_amt = total_receivable_amount - (coupon_sales_amt + cash_sales_amt)
    if non_cash_receivable_amt:
        sales_journal=Journal(date=shift.date,details=details,amount=non_cash_receivable_amt,dr=debtor.id,cr=sales_acc.id,created_by=session['user_id'])
        db.session.add(sales_journal)
        db.session.flush()
    return True


def post_coupon_sales_journal(shift_id):
    """ Post coupon sales journal """
    shift = Shift.query.get(shift_id)
    coupons = db.session.query(Coupon,CouponSale,Product).filter(and_(Coupon.id==CouponSale.coupon_id,CouponSale.shift_id==shift_id,CouponSale.product_id==Product.id,CouponSale.coupon_id==coupon_id)).all()
    sales_acc = Account.query.filter_by(account_name="Fuel Sales").first()
    details = "Shift {} coupon sales".format(shift_id)
    for sale in coupons:
        amt =sum([(i[0].coupon_qty* i[1].qty * i[2].selling_price )for i in coupon_sales ])
        if amt:
            coupon_journal=Journal(date=shift.date,details=details,amount=amt,dr=sale[3].account_id,cr=sales_acc.id,created_by=session['user_id'])
            db.session.add(coupon_journal)
            db.session.flush()
    return True

def post_cash_sales_journal(shift_id):
    """ Post cash sales (sales receipts) journal """
    shift = Shift.query.get(shift_id)
    sales_receipts = SaleReceipt.query.filter_by(shift_id=shift_id).all() # use sum ?
    sales_acc = Account.query.filter_by(account_name="Fuel Sales").first()
    details = "Shift {} sales receipts".format(shift_id)
    for receipt in sales_receipts:
        cash_journal = Journal(date=shift.date,details=details,amount=receipt.amount,dr=receipt.account_id,cr=sales_acc.id,created_by=session['user_id'])
        db.session.add(cash_journal)
        db.session.flush()
    return True

def post_lubes_sales_journal(shift_id):
    """ Post sales journal for Lube sales """
    shift = Shift.query.get(shift_id)
    cash_up = LubesCashUp.query.filter_by(shift_id=shift_id).first()
    amount = cash_up.expected_amount
    sales_acc = Account.query.filter_by(account_name="Lube Sales").first()
    debtor = Account.query.filter_by(account_name="Cash").first()
    details = "Shift {} lubricants sales".format(shift_id)
    sales_journal=Journal(date=shift.date,details=details,amount=amount,dr=debtor.id,cr=sales_acc.id,created_by=session['user_id'])
    db.session.add(sales_journal)
    db.session.flush()
    return True

def post_all_shift_journals(shift_id):
    """ Post all Journals """
    post_cash_sales_journal(shift_id)
    post_coupon_sales_journal(shift_id)
    post_fuel_sales_journals(shift_id)
    post_fuel_variance_journals(shift_id)
    post_lubes_sales_journal(shift_id)

    return True

def opening_balance(date,account_id):
    """ calculate ledger opening balance for the period"""
    account = Account.query.get(account_id)
    if account.entry =="DR":
        receipts = Journal.query.filter(and_(Journal.dr == account.id,Journal.date < date)).all()
        payouts = Journal.query.filter(and_(Journal.cr == account.id,Journal.date < date)).all()
        
        balance = sum([i.amount for i in receipts]) - sum([i.amount for i in payouts])
    else:
        payouts = Journal.query.filter(and_(Journal.dr == account_id,Journal.date < date)).all()
        receipts = Journal.query.filter(and_(Journal.cr == account_id,Journal.date < date)).all()
        
        balance = sum([i.amount for i in receipts]) - sum([i.amount for i in payouts])

    return balance
    