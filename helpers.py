import os
import urllib.request
from flask import redirect, render_template, request, session,flash,url_for
from functools import wraps
from models import *
from collections import *
from sqlalchemy import and_ , or_
from datetime import timedelta

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

        if session.get("role_id") != 1:
            flash("Access not allowed,Log in as the Admin !!")
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function

def start_shift_first(f):

    """

    Decorate routes to check if a shift has started
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
            return redirect(url_for('ss26'))


        return f(*args, **kwargs)

    return decorated_function


def lubes_cash_up(f):

    """

    Decorate routes if user attempts to do a cash up on lubes already done
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    """

    @wraps(f)

    def decorated_function(*args, **kwargs):
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_id = current_shift.id
        check_cash_up = LubesCashUp.query.filter_by(shift_id=shift_id).first()
        if check_cash_up:
            flash("Cash up for lubes done for this shift")
            return redirect(url_for('ss26'))


        return f(*args, **kwargs)

    return decorated_function


def sales_before_receipts(shift_id,product_id):
    products = Product.query.get(product_id)
    product_id = products.id
    invoices = Invoice.query.filter(and_(Invoice.shift_id == shift_id,Invoice.product_id == product_id)).all()
    total__invoices = sum([invoice.qty for invoice in invoices])
    price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = price.selling_price
    
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
    price = price.selling_price
    amount = sales * price
    return amount

def receipt_product_qty(amount,shift_id,product_id):
    product = Product.query.get(product_id)
    product_id = product_id
    price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id)).first()
    price = price.selling_price
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
            return shifts[2].date
            
        else:
            return date
    else:
        return date

def product_sales_litres(shift_id,prev_shift_id):
    """ Calculates Sales per fuel product e.g Total Petrol Sales per shift"""
    products = Product.query.all()
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
            product_sales[product.name] = (sales,prices[1])
    
    
    return product_sales

    
def fuel_daily_profit_report(start_date,end_date):
    """ fuel day-to-day profit"""
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    if shifts:
        dates = [i.date for i in shifts ]
        profit = {}
        for date in dates:
            current_shift= Shift.query.filter_by(date=date).order_by(Shift.id.desc()).first()
            prev_date = date- timedelta(days=1)
            prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
            if prev_shift and current_shift:
                shift_id = current_shift.id
                prev_shift_id = prev_shift.id
                litres = product_sales_litres(shift_id,prev_shift_id)
                sales = sum([litres[i][0]*litres[i][1].selling_price for i in litres])
                cost = sum([litres[i][0]*litres[i][1].cost_price for i in litres])
                profit[date]= (sales - cost)
            else :
                
                pass

        return profit
    else:
        return False


def fuel_mnth_profit_report(start_date,end_date):
    """fuel month to month profit"""
    days = fuel_daily_profit_report(start_date,end_date)
    report = {}
    for day in days:
        month = day.month
        if month in report:
            report[month] += days[day]
        else:
            report[month] = days[day]
    return report

def fuel_product_profit_statement(start_date,end_date):
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    if shifts:
        dates = [i.date for i in shifts]
        profit = {}
        for date in dates:
            current_shift= Shift.query.filter_by(date=date).order_by(Shift.id.desc()).first()
            prev_date = date- timedelta(days=1)
            prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
            if prev_shift and current_shift:
                shift_id = current_shift.id
                prev_shift_id = prev_shift.id
                product = product_sales_litres(shift_id,prev_shift_id)
                profit[date] = {i:[product[i][0],product[i][1].selling_price,product[i][1].cost_price,product[i][1].selling_price-product[i][1].cost_price] for i in product}
                
            else :
                
                pass

        return profit
    else:
        return False

def get_tank_variance(start_date,end_date,tank_id):
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    tank_dips={}
    cumulative = 0
    cumulativeP = 0
    for shift in shifts:
        prev = Shift.query.filter(Shift.id < shift.id).order_by(Shift.id.desc()).first()
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
            delivery = Fuel_Delivery.query.filter(and_(Fuel_Delivery.shift_id==shift.id,Fuel_Delivery.tank_id==tank_id)).all()
            deliveries = sum([i.qty for i in delivery])
            tank_sales = prev_shift_dip+deliveries-current_shift_dip
            shrinkage2sales = (pump_sales-tank_sales)
            shrinkage2salesP = shrinkage2sales/pump_sales *100 if pump_sales !=0 else 0
            cumulative = cumulative + shrinkage2sales
            cumulativeP = cumulativeP + shrinkage2salesP
            tank_dips[shift.id]=[shift.date,prev_shift_dip,current_shift_dip,deliveries,tank_sales,pump_sales,shrinkage2sales,shrinkage2salesP,cumulative,cumulativeP]

    return tank_dips




def cash_sales(amount,customer_id,shift_id,date):
    """ Calculates invoices as per amount, as cash sales usually lack product information"""
    amount =  amount
    products = Product.query.filter_by(product_type="Fuels").all()
    products_qty={}
    for product in products:
        product_qty = receipt_product_qty(amount,shift_id,product.id)
        if product_qty >1:
            products_qty[product.name]=product_qty
        else:
            pass
    
    for prod in products_qty:
        product = Product.query.filter_by(name=prod).first()
        sales_price = get_product_price(shift_id,product.id)
        if products_qty[prod]*sales_price < amount:
            qty = products_qty[prod]
            invoice = Invoice(date=date,product_id=product.id,shift_id=shift_id,customer_id=customer_id,qty=qty,price=sales_price)
            db.session.add(invoice)
            inv_amt = float(products_qty[prod] * sales_price)
            products_qty[prod] = products_qty[prod]-qty
        elif products_qty[prod]*sales_price > amount:
            qty = amount/sales_price
            invoice = Invoice(date=date,product_id=product.id,shift_id=shift_id,customer_id=customer_id,qty=qty,price=sales_price)
            db.session.add(invoice)
            break
        elif products_qty[prod] < 1:
            break

    

    return True


def lube_sales(shift_id,prev_shift_id):
    """Calcuates lube sales per shift"""
    products = LubeProduct.query.all()
    product_sales = {}

    for product in products:
            prev = LubeQty.query.filter(and_(LubeQty.shift_id == prev_shift_id,LubeQty.product_id== product.id)).first()
            curr = LubeQty.query.filter(and_(LubeQty.shift_id == shift_id,LubeQty.product_id== product.id)).first()
            if prev and curr: # check if previous shift exists
                sales = ( prev.qty + curr.delivery_qty)-curr.qty
                cost_price = product.cost_price
                selling_price = product.selling_price
                mls = product.mls
                delivery = curr.delivery_qty
                #remove spaces fron names so as to render modals correctly
                modal_name = product.name.replace(" ","")
                product_sales[product.name]= (prev.qty,curr.qty,sales,cost_price,selling_price,mls,delivery,modal_name)
            else:
                pass

    return product_sales

def get_month_day1(end_date):
    """fuel month to date  sales"""
    today = end_date
    month =today.month
    year = today.year
    first_day = date(year,month,1)
    return first_day


def fuel_daily_sales(start_date,end_date):
    """fuel day to day  sales"""
    
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    daily_sales = {}
    dates = [i.date for i in shifts]
    oneday = timedelta(days=1)
    for d in dates:
        current_shift= Shift.query.filter_by(date=d).order_by(Shift.id.desc()).first()
        prev_date = d -oneday
        prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
        if current_shift and prev_shift:
            shift_id = current_shift.id
            prev_shift_id = prev_shift.id
            product_sales = product_sales_litres(shift_id,prev_shift_id)
            total = sum([product_sales[i][0] for i in product_sales])
            daily_sales[d]= total
        
        else:

            pass

    return daily_sales
    


def fuel_mnth_sales(start_date,end_date):
    """fuel month to month sales"""
    days = fuel_daily_sales(start_date,end_date)
    report = {}
    for day in days:
        month = day.month
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
        month = day.month
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
    days= (end_date - start_date).days
    avg = total/days

    return avg

def lubes_daily_sales(start_date,end_date):
    """Lubes  sales between particular dates"""

    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    daily_sales = {}
    oneday = timedelta(days=1)
    dates = [i.date for i in shifts]

    for d in dates:
        current_shift= Shift.query.filter_by(date=d).order_by(Shift.id.desc()).first()
        prev_date = d -oneday
        prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
        if current_shift and prev_shift:
            shift_id = current_shift.id
            prev_shift_id = prev_shift.id
            product_sales = lube_sales(shift_id,prev_shift_id)
            total = sum([product_sales[i][2]*product_sales[i][5] for i in product_sales])/1000
            daily_sales[d]= total


    return daily_sales
    

def lubes_sales_avg(start_date,end_date):
    """Lubes average for the current dates"""
    shifts = Shift.query.filter(Shift.date.between(start_date,end_date)).all()
    if shifts:
        daily_sales = lubes_daily_sales(start_date,end_date)
        total = sum([daily_sales[i] for i in daily_sales ])
        end_date= shifts[-1].date
        start_date= shifts[0].date
        days= (end_date - start_date).days
        avg = total/days

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
        if prev_shift_reading and current_shift_reading:
            prev_shift_reading = prev_shift_reading.litre_reading,prev_shift_reading.money_reading
            current_shift_reading = current_shift_reading.litre_reading,current_shift_reading.money_reading
            pump_readings[pump.name]=[prev_shift_reading,current_shift_reading]
    return pump_readings

def get_tank_dips(shift_id,prev_shift_id):
    tank_dips = {}
    tanks = Tank.query.all()
    for tank in tanks:
        prev_shift_dip = prev_shift_dip.dip
        current_shift_dip = current_shift_dip.dip
        curr_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==shift_id,Tank.id==tank.id)).all()
        prev_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==prev_shift_id,Tank.id==tank.id)).all()
        pump_sales = sum([i[2].litre_reading for i in curr_pump_reading])-sum([i[2].litre_reading for i in prev_pump_reading])
        
        prev_shift_dip = TankDip.query.filter(and_(TankDip.shift_id ==prev_shift_id,TankDip.tank_id == tank.id)).first()
        current_shift_dip= TankDip.query.filter(and_(TankDip.shift_id == shift_id,TankDip.tank_id == tank.id)).first()
        delivery = Fuel_Delivery.query.filter(and_(Fuel_Delivery.shift_id==shift_id,Fuel_Delivery.tank_id==tank.id)).all()
        deliveries = sum([i.qty for i in delivery])
        tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales,deliveries]
    return tank_dips


    product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
    cash_account = Customer.query.filter_by(name="Cash").first()
    customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Invoice.customer_id != cash_account.id))
    sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
    total_sales_ltr= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
    total_sales_amt= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1].selling_price for product in product_sales_ltr])
    sales_breakdown["Cash"] = total_sales_amt- sum([sales_breakdown[i] for i in sales_breakdown])
    expenses = db.session.query(PayOut,Account).filter(and_(PayOut.pay_out_account== Account.id,PayOut.shift_id==shift_id)).all()
    total_cash_expenses = sum([i[0].amount for i in expenses ])
    cash_up = CashUp.query.filter_by(shift_id=shift_id).first()
    products = Product.query.all()
    customers = Customer.query.all()
    cash_customers = Customer.query.filter_by(account_type="Cash")
    accounts = Account.query.all()
    end_date = current_shift.date
    avg_sales = fuel_sales_avg(get_month_day1(end_date),end_date)
    daily_sales = fuel_daily_sales(get_month_day1(end_date),end_date) 
    mnth_sales = sum([daily_sales[i] for i in daily_sales])
    lubes_daily_sale = lubes_daily_sales(get_month_day1(end_date),end_date)
    lubes_mnth_sales = sum([lubes_daily_sale[i] for i in lubes_daily_sale])
    lube_avg = lubes_sales_avg(get_month_day1(end_date),end_date)
    
    return True
