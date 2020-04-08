import os

from flask import Flask, session, render_template,flash,request,redirect,url_for,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *
from models import *
from random import randint
app = Flask(__name__,template_folder = "templates")

# Set Database URL
#DATABASE_URL ="postgres://vyltpsivhqeaun:c0bb13175e810c1dcb143e03d1dc47b2ebaf46e095d9d6dfc8979d19f6a48e14@ec2-50-16-197-244.compute-1.amazonaws.com:5432/d3ud9s5a665gva"
DATABASE_URL ="postgres://localhost/ss26"
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.urandom(24)
db.init_app(app)


@app.route("/",methods=["GET","POST"])
@login_required
def dashboard():
    """ Dashboard"""
    return render_template("dashboard.html")

@app.route("/login",methods=["GET","POST"])
def login():
        """Log In User"""
        session.clear()

    #check login crenditials

        if request.method == "POST":

                username = request.form.get("username")
                password = request.form.get("password")
                user = User.query.filter_by(username=request.form.get("username")).first()

                if username != user.username or not check_password_hash(user.password,password):
                        flash("Username/Password Not Correct !!")
                        return redirect(url_for('login'))
                else:
                        session["user_id"] = user.id
                        return redirect(url_for('dashboard'))
        else:
                return render_template("login.html")

@app.route("/start_shift_update",methods=["GET","POST"])
@login_required
@end_shift_first
def start_shift_update():
        "Start Update of Shift Figures"
        if request.method == "POST":
                day= request.form.get("date")
                shift_daytime = request.form.get("shift")
                pumps = Pump.query.all()
                tanks = Tank.query.all()
                db.session.query(Shift_Underway).filter(Shift_Underway.id == 1).update({Shift_Underway.state: True}, synchronize_session = False)
                db.session.commit()
                shift = Shift(date=day,daytime=shift_daytime)
                db.session.add(shift)
                db.session.commit()
                current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                prev_shift_id = int(shift_id)-1
                date = current_shift.date
                for pump in pumps:
                        tank = Pump.query.filter_by(id=pump.id).first()
                        tank_id = tank.tank_id
                        product = db.session.query(Tank,Product).filter(and_(Tank.product_id == Product.id,Tank.id == tank_id)).first()
                        product = Product.query.filter_by(name=str(product[1])).first()
                        product_id = product.id
                        pump_readings =PumpReading(date=date,product_id=product_id,litre_reading=0,money_reading=0,pump_id=pump.id,shift_id=shift_id)
                        db.session.add(pump_readings)
                        db.session.commit()
                for tank in tanks:
                        tank_dip = TankDip(date=date,dip=0,tank_id=tank.id,shift_id=shift_id)
                        db.session.add(tank_dip)
                        product = db.session.query(Tank,Product).filter(and_(Tank.product_id == Product.id,Tank.id == tank_id)).first()
                        product = Product.query.filter_by(name=str(product[1])).first()
                        product_id = product.id
                        fuel_delivery = Fuel_Delivery(date=date,shift_id=shift_id,tank_id=tank.id,qty=0,product_id=product_id,document_number='0000')
                        db.session.add(fuel_delivery)
                        db.session.commit()
                prev_prices = db.session.query(Product,Price).filter(and_(Product.id == Price.product_id,Price.shift_id == prev_shift_id)).all()
                for i in prev_prices:
                        price = Price(date=date,shift_id=shift_id,product_id=i[0].id,cost_price=i[1].cost_price,selling_price=i[1].selling_price)
                        db.session.add(price)
                        db.session.commit()
                flash('Shift Started')
                return redirect(url_for('ss26'))

        else:
                return render_template("start_shift_update.html")

@app.route("/end_shift_update",methods=["GET","POST"])
@login_required
@start_shift_first
def end_shift_update():
        "End Update of Shift Figures"
        if request.method == "POST":
                db.session.query(Shift_Underway).filter(Shift_Underway.id == 1).update({Shift_Underway.state: False}, synchronize_session = False)
                db.session.commit()
                flash('Shift Ended')
                return redirect(url_for('dashboard'))

        else:
                return render_template("start_shift_update.html")

        

@app.route("/readings_entry",methods=["GET","POST"])
@login_required
def readings_entry():
        """Updates after shift update"""
        pumps = Pump.query.all()
        tanks= Tank.query.all()
        products= Product.query.all()
        customers= Customer.query.all()
        cash_customers = Customer.query.filter_by(account_type="Cash")
        accounts =Account.query.all()
        return render_template("readings_entry.html",tanks=tanks,pumps=pumps,products=products,customers=customers,accounts=accounts,cash_customers=cash_customers)

@app.route("/price_change",methods=["GET","POST"])
@login_required
def price_change():
        """Price Change outside shift update"""
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        product= int(request.form.get("product"))
        cost_price = request.form.get("cost_price")
        selling_price = request.form.get("selling_price")
        price = Price(date=date,shift_id=shift_id,product_id=product,cost_price=cost_price,selling_price=selling_price)
        db.session.add(price)
        db.session.commit()
        return redirect(url_for('readings_entry'))

@app.route("/pump_readings_entry",methods=["GET","POST"])
@login_required
@start_shift_first
def pump_readings_entry():
        """Enter readings for pumps """
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        pump_id= request.form.get("pump_name")
        tank = Pump.query.filter_by(id=pump_id).first()
        tank_id = tank.tank_id
        product = db.session.query(Tank,Product).filter(and_(Tank.product_id == Product.id,Tank.id == tank_id)).first()
        product = Product.query.filter_by(name=str(product[1])).first()
        product_id = product.id
        litre_reading = int(request.form.get("litre_reading"))
        money_reading = int(request.form.get("money_reading"))
        if money_reading:
                pump_readings = PumpReading(date=date,product_id=product_id,litre_reading=litre_reading,money_reading=money_reading,pump_id=pump_id,shift_id=shift_id)
                db.session.add(pump_readings)
                db.session.commit()
                return redirect(url_for('readings_entry'))
        else:
                pump_readings = PumpReading(date=date,product_id=product_id,litre_reading=litre_reading,pump_id=pump_id,shift_id=shift_id)
                db.session.add(pump_readings)
                db.session.commit()
                return redirect(url_for('readings_entry'))


@app.route("/tank_dips_entry",methods=["POST"])
@login_required
@start_shift_first
def tank_dips_entry():
        """Enter Dips for Tanks """
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        tank_name= request.form.get("tank_name")
        dip =request.form.get("tank_dip")
        tank_dip = TankDip(date=date,dip=dip,tank_id=tank_name,shift_id=shift_id)
        db.session.add(tank_dip)
        db.session.commit()
        return redirect(url_for('readings_entry'))


@app.route("/fuel_delivery",methods=["POST"])
@login_required
@start_shift_first
def fuel_delivery():
        """Enter Fuel Delivery"""   
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        document_number = request.form.get("document_number")
        tank_id= request.form.get("tank_name")
        qty =request.form.get("litres_delivered")
        product_id= request.form.get("product")
        fuel_delivery = Fuel_Delivery(date=date,shift_id=shift_id,tank_id=tank_id,qty=qty,product_id=product_id,document_number=document_number)
        db.session.add(fuel_delivery)
        db.session.commit()
        return redirect(url_for('readings_entry'))






@app.route("/payouts",methods=["POST"])
@login_required
@start_shift_first
def pay_outs():
        """payouts"""
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        amount= request.form.get("amount")
        source_account= request.form.get("source_account")
        pay_out_account= request.form.get("pay_out_account")
        pay_out = PayOut(source_account=source_account,pay_out_account=pay_out_account,date=date,shift_id=shift_id,amount=amount)
        db.session.add(pay_out)
        db.session.commit()
        return redirect(url_for('readings_entry'))

@app.route("/admin/manage_users",methods=["GET","POST"])
@login_required
@admin_required
def manage_users():
        """Managing Users"""
        if request.method == "GET":
                users_roles = db.session.query(User,Role).filter(Role.id == User.role_id).all()
                users= User.query.all()
                roles = Role.query.all()
                return render_template("manageusers.html",roles=roles,users_roles=users_roles,users=users)



@app.route("/manage_users/add_user",methods=["POST"])
@login_required
@admin_required
def add_user():
        """Add User"""
        user = User(username=request.form.get("username").capitalize(),password=request.form.get("password"),role_id=request.form.get("role"))
        user_exists = bool(User.query.filter_by(username=request.form.get("username").capitalize()).first())
        if user_exists:
                message = "User already exists, Try using another username!!"
                return render_template("error.html",message=message)
        else:
                db.session.add(user)
                db.session.commit()
                flash('User Successfully Added')
                return redirect(url_for('manage_users'))

@app.route("/manage_users/edit_user",methods=["POST"])
@login_required
@admin_required
def edit_user():
        """Edit User Information"""
        db.session.query(User).filter(User.username == request.form.get("username")).update({User.password: generate_password_hash(request.form.get("password"))}, synchronize_session = False)
        db.session.query(User).filter(User.username == request.form.get("username")).update({User.role_id: request.form.get("role")}, synchronize_session = False)
        db.session.commit()
        flash('User Successfully Updated')
        return redirect(url_for('manage_users'))

@app.route("/manage_users/delete_user",methods=["POST"])
@login_required
@admin_required
def delete_user():
        """Deletes Users"""
        user = db.session.query(User).get(int(request.form.get("users")))
        db.session.delete(user)  
        db.session.commit()
        flash('User Successfully Removed!!')
        return redirect(url_for('manage_users'))



@app.route("/admin/pump_list",methods=["GET","POST"])
@login_required
@admin_required
def pumps():
        """Pump List"""
        pump_tank = db.session.query(Tank,Pump).filter(Tank.id == Pump.tank_id).all()
        pumps =  Pump.query.all()
        tanks = Tank.query.all()
        return render_template("pumps.html",pumps=pumps,pump_tank=pump_tank,tanks=tanks)
        

@app.route("/add_pump",methods=["POST"])
@login_required
@admin_required
def add_pump():

        """Add Pump"""
        pump = Pump(name=request.form.get("pump_name").capitalize(),tank_id=request.form.get("tank"))
        db.session.add(pump)
        db.session.commit()
        flash('Pump Successfully Added !!')
        return redirect(url_for('pumps'))


@app.route("/admin/delete_pump",methods=["POST"])
@login_required
@admin_required
def delete_pump():
        """Delete Pump"""
        pump = db.session.query(Pump).get(int(request.form.get("pumps")))
        db.session.delete(pump)  
        db.session.commit()
        flash('Pump Successfully Removed!!')
        return redirect(url_for('pumps'))

@app.route("/add_tank",methods=["POST"])
@login_required
@admin_required
def add_tank():
        """Add Tank"""
        tank = Tank(name=request.form.get("tank_name").capitalize(),product_id=request.form.get("product"))
        db.session.add(tank)
        db.session.commit()

        return redirect(url_for('tanks'))

@app.route("/admin/delete_tank",methods=["POST"])
@login_required
@admin_required
def delete_tank():
        """Delete Tank"""
        tank = db.session.query(Tank).get(int(request.form.get("tanks")))
        db.session.delete(tank)  
        db.session.commit()
        flash('Tank Successfully Removed!!')
        return redirect(url_for('tanks'))

@app.route("/admin/tank_list",methods=["GET","POST"])
@login_required
@admin_required
def tanks():
        """Tank List"""
        tank_product = db.session.query(Product,Tank).filter(Product.id == Tank.product_id).all()
        tanks = Tank.query.all()
        products = Product.query.all()
        return render_template("tanks.html",tanks=tanks,products=products,tank_product=tank_product)

@app.route("/admin/product_list",methods=["GET","POST"])
@login_required
@admin_required
def products():
        """Product List"""
        products = Product.query.all()
        return render_template("products.html",products=products)

@app.route("/add_product",methods=["POST"])
@login_required
@admin_required
def add_product():
        """Add Product"""
        product = Product(name=request.form.get("product_name").capitalize(),price=request.form.get("price"),product_type=request.form.get("product_type"))
        db.session.add(product)
        db.session.commit()
        flash("Product Added !!")
        return redirect(url_for('products'))

@app.route("/admin/delete_product",methods=["POST"])
@login_required
@admin_required
def delete_product():
        """Delete Product"""
        product = db.session.query(Product).get(int(request.form.get("products")))
        db.session.delete(product)  
        db.session.commit()
        flash('Tank Successfully Removed!!')
        return redirect(url_for('products'))

@app.route("/admin/customers",methods=["GET","POST"])
@login_required
@admin_required
def customers():
        """Managing Customers"""
        customers= Customer.query.all()
        return render_template("customers.html",customers=customers)



@app.route("/customers/add_customer",methods=["POST"])
@login_required
@admin_required
def add_customer():
        """Add Customer"""
        customer = Customer(name=request.form.get("name").capitalize(),account_type=request.form.get("type"),phone_number=request.form.get("phone"),contact_person=request.form.get("contact_person").capitalize())
        customer_exists = bool(Customer.query.filter_by(name=request.form.get("name")).first())
        if customer_exists:
                flash("User already exists, Try using another username!!")
                return redirect(url_for('customers'))
        else:
                account_type = request.form.get("type").capitalize()
                account_name = request.form.get("name").capitalize()
                if account_type == "Non-Cash":
                        db.session.add(customer)
                        db.session.commit()
                        flash('Customer Successfully Added')
                        return redirect(url_for('customers'))
                else:
                        db.session.add(customer)
                        db.session.commit()
                        account = Account(account_name=account_name,account_category=account_type)
                        db.session.commit()
                        flash('Customer Successfully Added')
                        return redirect(url_for('customers'))


@app.route("/customers/edit_customer",methods=["POST"])
@login_required
@admin_required
def edit_customer():
        """Edit Customer Information"""
        db.session.query(Customer).filter(Customer.name == request.form.get("name")).update({Customer.phone_number: request.form.get("phone")}, synchronize_session = False)
        db.session.query(Customer).filter(Customer.name == request.form.get("name")).update({Customer.contact_person: request.form.get("contact_person")}, synchronize_session = False)
        db.session.commit()
        flash('Customer Successfully Updated')
        return redirect(url_for('customers'))

@app.route("/customers/delete_customer",methods=["POST"])
@login_required
@admin_required
def delete_customer():
        """Deletes Customers"""
        customer = db.session.query(Customer).get(int(request.form.get("customers")))
        db.session.delete(customer)  
        db.session.commit()
        flash('Customer Successfully Removed!!')
        return redirect(url_for('customers'))

@app.route("/admin/suppliers",methods=["GET","POST"])
@login_required
@admin_required
def suppliers():
        """Managing Suppliers"""
        suppliers= Supplier.query.all()
        return render_template("suppliers.html",suppliers=suppliers)



@app.route("/suppliers/add_supplier",methods=["POST"])
@login_required
@admin_required
def add_supplier():
        """Add Supplier"""
        supplier = Supplier(name=request.form.get("name").capitalize(),phone_number=request.form.get("phone"),contact_person=request.form.get("contact_person").capitalize())
        supplier_exists = bool(Supplier.query.filter_by(name=request.form.get("name")).first())
        if supplier_exists:
                flash("Supplier already exists, Try using another username!!")
                return redirect(url_for('suppliers'))
        else:
                db.session.add(supplier)
                db.session.commit()
                flash('Supplier Successfully Added')
                return redirect(url_for('suppliers'))

@app.route("/suppliers/edit_supplier",methods=["POST"])
@login_required
@admin_required
def edit_supplier():
        """Edit Supplier Information"""
        db.session.query(Supplier).filter(Supplier.name == request.form.get("name")).update({Supplier.phone_number: request.form.get("phone")}, synchronize_session = False)
        db.session.query(Supplier).filter(Supplier.name == request.form.get("name")).update({Supplier.contact_person: request.form.get("contact_person")}, synchronize_session = False)
        db.session.commit()
        flash('Supplier Successfully Updated')
        return redirect(url_for('suppliers'))

@app.route("/suppliers/delete_supplier",methods=["POST"])
@login_required
@admin_required
def delete_supplier():
        """Deletes Supplier"""
        supplier = db.session.query(Supplier).get(int(request.form.get("suppliers")))
        db.session.delete(supplier)  
        db.session.commit()
        flash('Supplier Successfully Removed!!')
        return redirect(url_for('suppliers'))



@app.route("/admin/accounts",methods=["GET","POST"])
@login_required
@admin_required
def accounts():
        """Managing Accounts"""
        accounts= Account.query.all()
        return render_template("accounts.html",accounts=accounts)

@app.route("/admin/delete_account",methods=["POST"])
@login_required
@admin_required
def delete_account():
        """Deletes Account"""
        account = db.session.query(Account).get(int(request.form.get("accounts")))
        db.session.delete(account)  
        db.session.commit()
        flash('Account Successfully Removed!!')
        return redirect(url_for('accounts'))

@app.route("/admin/add_accounts",methods=["POST"])
@login_required
@admin_required
def add_account():
        """Add Account"""
        account = Account(account_name=request.form.get("name").capitalize(),account_category=request.form.get("category"))
        account_exists = bool(Account.query.filter_by(account_name=request.form.get("name")).first())
        if account_exists:
                flash("Account already exists, Try using another username!!")
                return redirect(url_for('accounts'))
        else:
                db.session.add(account)
                db.session.commit()
                flash('Account Successfully Added')
                return redirect(url_for('accounts'))




@app.route("/driveway",methods=["GET","POST"])
@login_required
def get_driveway():

        """Query Shift Driveways for a particular day """
        if request.method == "POST":
        
                shift_daytime = request.form.get("shift")
                date = request.form.get("date")
                current_shift= Shift.query.filter(and_(Shift.date == date,Shift.daytime == shift_daytime)).first()
                shift_id = current_shift.id
                prev_shift_id = int(shift_id)-1
                pump_readings = {}
                pumps = Pump.query.all()
                for pump in pumps:

                        prev_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev_shift_id,PumpReading.pump_id == pump.id)).first()
                        prev_shift_reading = prev_shift_reading.litre_reading,prev_shift_reading.money_reading
                        current_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == shift_id,PumpReading.pump_id == pump.id)).first()
                        current_shift_reading = current_shift_reading.litre_reading,current_shift_reading.money_reading
                        pump_readings[pump.name]=[prev_shift_reading,current_shift_reading]
                tank_dips = {}
                tanks = Tank.query.all()
                for tank in tanks:
                        curr_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==shift_id,Tank.id==tank.id)).all()
                        prev_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==prev_shift_id,Tank.id==tank.id)).all()
                        pump_sales = sum([i[2].litre_reading for i in curr_pump_reading])-sum([i[2].litre_reading for i in prev_pump_reading])
                        prev_shift_dip = TankDip.query.filter(and_(TankDip.shift_id ==prev_shift_id,TankDip.tank_id == tank.id)).first()
                        prev_shift_dip = prev_shift_reading.dip
                        current_shift_dip= TankDip.query.filter(and_(TankDip.shift_id ==shift_id,TankDip.tank_id == tank.id)).first()
                        current_shift_dip = current_shift_reading.dip
                        tank_dips[tank.name]=[prev_shift_dip,current_shift_dip]
                product_sales = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == shift_id)).all()
                petrol_sales = [sum([i[1].litre_reading for i in product_sales if i[0].name =="Petrol" ]),db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.name=="Petrol")).all()]
                diesel_sales = [sum([i[1].litre_reading for i in product_sales if i[0].name =="Diesel" ]),db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.name=="Diesel")).all()]
                customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id))
                sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer refer to helpers
                return render_template("get_driveway.html",sales_breakdown=sales_breakdown,shift_number=shift_id,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,pumps=pumps,tanks=tanks,petrol_sales=petrol_sales,diesel_sales=diesel_sales)
        else:
                current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                prev_shift_id = int(shift_id)-1
                pump_readings = {}
                pumps = Pump.query.all()
                for pump in pumps:
                        prev_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev_shift_id,PumpReading.pump_id == pump.id)).first()
                        prev_shift_reading = prev_shift_reading.litre_reading,prev_shift_reading.money_reading
                        current_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == shift_id,PumpReading.pump_id == pump.id)).first()
                        current_shift_reading = current_shift_reading.litre_reading,current_shift_reading.money_reading
                        pump_readings[pump.name]=[prev_shift_reading,current_shift_reading]
                tank_dips = {}
                tanks = Tank.query.all()
                for tank in tanks:
                        curr_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==shift_id,Tank.id==tank.id)).all()
                        prev_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==prev_shift_id,Tank.id==tank.id)).all()
                        pump_sales = sum([i[2].litre_reading for i in curr_pump_reading])-sum([i[2].litre_reading for i in prev_pump_reading])
                        prev_shift_dip = TankDip.query.filter(and_(TankDip.shift_id ==prev_shift_id,TankDip.tank_id == tank.id)).first()
                        prev_shift_dip = prev_shift_dip.dip
                        current_shift_dip= TankDip.query.filter(and_(TankDip.shift_id == shift_id,TankDip.tank_id == tank.id)).first()
                        current_shift_dip = current_shift_dip.dip
                        tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales]
                prev_product_reading = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == prev_shift_id)).all()
                curr_product_reading = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == shift_id)).all()
                petrol_sales = [sum([i[1].litre_reading for i in curr_product_reading if i[0].name =="Petrol" ])-sum([i[1].litre_reading for i in prev_product_reading if i[0].name =="Petrol" ]),db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.name=="Petrol")).all()]
                diesel_sales = [sum([i[1].litre_reading for i in curr_product_reading if i[0].name =="Diesel" ])-sum([i[1].litre_reading for i in prev_product_reading if i[0].name =="Diesel" ]),db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.name=="Diesel")).all()]
                customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id))
                sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer refer to helpers
                expenses = db.session.query(PayOut,Account).filter(and_(PayOut.pay_out_account== Account.id,PayOut.shift_id==shift_id)).all()
                total_cash_expenses = sum([i[0].amount for i in expenses if i[1].name=='Cash' ])
                cash_up = CashUp.query.filter_by(shift_id=shift_id).first()
                return render_template("get_driveway.html",cash_up=cash_up,expenses=expenses,sales_breakdown=sales_breakdown,shift_number=shift_id,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,pumps=pumps,tanks=tanks,diesel_sales=diesel_sales,petrol_sales=petrol_sales)



@app.route("/ss26",methods=["GET"])
@login_required
def ss26():

        """UPDATE DRIVEWAY DATA """
               
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        prev_shift_id = int(shift_id)-1
        pump_readings = {}
        pumps = Pump.query.all()
        for pump in pumps:
                prev_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev_shift_id,PumpReading.pump_id == pump.id)).first()
                prev_shift_reading = prev_shift_reading.litre_reading,prev_shift_reading.money_reading
                current_shift_reading = PumpReading.query.filter(and_(PumpReading.shift_id == shift_id,PumpReading.pump_id == pump.id)).first()
                current_shift_reading = current_shift_reading.litre_reading,current_shift_reading.money_reading
                pump_readings[pump.name]=[prev_shift_reading,current_shift_reading]
        tank_dips = {}
        tanks = Tank.query.all()
        for tank in tanks:
                curr_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==shift_id,Tank.id==tank.id)).all()
                prev_pump_reading  = db.session.query(Tank,Pump,PumpReading).filter(and_(Tank.id == Pump.tank_id,Pump.id == PumpReading.pump_id,PumpReading.shift_id==prev_shift_id,Tank.id==tank.id)).all()
                pump_sales = sum([i[2].litre_reading for i in curr_pump_reading])-sum([i[2].litre_reading for i in prev_pump_reading])
                prev_shift_dip = TankDip.query.filter(and_(TankDip.shift_id ==prev_shift_id,TankDip.tank_id == tank.id)).first()
                prev_shift_dip = prev_shift_dip.dip
                current_shift_dip= TankDip.query.filter(and_(TankDip.shift_id == shift_id,TankDip.tank_id == tank.id)).first()
                current_shift_dip = current_shift_dip.dip
                tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales]
        prev_product_reading = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == prev_shift_id)).all()
        curr_product_reading = db.session.query(Product,PumpReading).filter(and_(Product.id == PumpReading.product_id,PumpReading.shift_id == shift_id)).all()
        petrol_sales = [sum([i[1].litre_reading for i in curr_product_reading if i[0].name =="Petrol" ])-sum([i[1].litre_reading for i in prev_product_reading if i[0].name =="Petrol" ]),db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.name=="Petrol")).all()]
        diesel_sales = [sum([i[1].litre_reading for i in curr_product_reading if i[0].name =="Diesel" ])-sum([i[1].litre_reading for i in prev_product_reading if i[0].name =="Diesel" ]),db.session.query(Product,Price).filter(and_(Product.id==Price.product_id,Price.shift_id==shift_id,Product.name=="Diesel")).all()]
        customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id))
        sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
        total_sales_amt= petrol_sales[0]* petrol_sales[1][0][1].selling_price + diesel_sales[0]*diesel_sales[1][0][1].selling_price
        sales_breakdown["Cash"] = total_sales_amt- sum([sales_breakdown[i] for i in sales_breakdown])
        expenses = db.session.query(PayOut,Account).filter(and_(PayOut.pay_out_account== Account.id,PayOut.shift_id==shift_id)).all()
        total_cash_expenses = sum([i[0].amount for i in expenses if i[1].name=='Cash' ])
        cash_up = CashUp.query.filter_by(shift_id=shift_id).first()
        products = Product.query.all()
        customers = Customer.query.all()
        cash_customers = Customer.query.filter_by(account_type="Cash")
        accounts = Account.query.all()
        suppliers = []#Supplier.query.all()
        for i in suppliers:
                accounts.append(i)
        return render_template("ss26.html",products=products,accounts=accounts,cash_customers=cash_customers,customers=customers,cash_up=cash_up,total_cash_expenses=total_cash_expenses,expenses=expenses,sales_breakdown=sales_breakdown,shift_number=shift_id,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,pumps=pumps,tanks=tanks,diesel_sales=diesel_sales,petrol_sales=petrol_sales)

@app.route("/update_pump_litre_readings",methods=['POST'])
@login_required
@start_shift_first
def update_pump_litre_readings():

        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        pump = Pump.query.filter_by(name=request.form.get("pump"))
        pump_id = pump.id
        reading = request.form.get("litre_reading")
        db.session.query(PumpReading).filter(and_(PumpReading.pump_id == pump_id,PumpReading.shift_id== shift_id)).update({PumpReading.litre_reading: reading}, synchronize_session = False)
        db.session.commit()

        return redirect('ss26')

@app.route("/update_pump_money_readings",methods=['POST'])
@login_required
@start_shift_first
def update_pump_money_readings():

        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        pump = Pump.query.filter_by(name=request.form.get("pump"))# get pumpid
        pump_id = pump.id
        reading = request.form.get("money_reading")
        db.session.query(PumpReading).filter(and_(PumpReading.pump_id == pump_id,PumpReading.shift_id ==shift_id)).update({PumpReading.money_reading: reading}, synchronize_session = False)
        db.session.commit()

        return redirect('ss26')


@app.route("/update_tank_dips",methods=['POST'])
@login_required
@start_shift_first
def update_tank_dips():

        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        tank= Tank.query.filter_by(name=request.form.get("tank"))
        tank_id = tank.id
        tank_dip = request.form.get("tank_dip")
        db.session.query(TankDip).filter(and_(TankDip.tank_id == tank_id,TankDip.shift_id ==shift_id)).update({TankDip.dip: tank_dip}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_fuel_deliveries",methods=['POST'])
@login_required
@start_shift_first
def update_fuel_deliveries():

        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        tank= Tank.query.filter_by(name=request.form.get("tank"))
        tank_id = tank.id
        delivery = request.form.get("delivery")
        db.session.query(Fuel_Delivery).filter(and_(Fuel_Delivery.tank_id == tank_id,Fuel_Delivery.shift_id ==shift_id)).update({Fuel_Delivery.qty: delivery}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_cost_prices",methods=['POST'])
@login_required
@start_shift_first
def update_cost_prices():

        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        product= Product.query.filter_by(name=request.form.get("product")).first()
        cost_price = request.form.get("cost_price")
        db.session.query(Price).filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).update({Price.cost_price: cost_price}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_selling_prices",methods=['POST'])
@login_required
@start_shift_first
def update_selling_prices():

        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_id = current_shift.id
        product= Product.query.filter_by(name=request.form.get("product")).first()
        selling_price = request.form.get("selling_price")
        db.session.query(Price).filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).update({Price.selling_price: selling_price}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_shift_date",methods=['POST'])
@login_required
@start_shift_first
def update_shift_date():

        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_id = current_shift.id
        date = request.form.get("date")
        db.session.query(Shift).filter(Shift.id==shift_id).update({Shift.date: date}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_shift_daytime",methods=['POST'])
@login_required
@start_shift_first
def update_shift_daytime():

        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_id = current_shift.id
        date = request.form.get("shift")
        db.session.query(Shift).filter(Shift.id==shift_id).update({Shift.daytime: date}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/customer_sales",methods=["POST"])
@login_required
@start_shift_first
def customer_sales():
        """Sales Invoices"""
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        vehicle_number= request.form.get("vehicle_number").capitalize()
        driver_name= request.form.get("driver_name").capitalize()
        sales_price= request.form.get("sales_price")
        product = request.form.get("product")
        qty= request.form.get("qty")
        customer_id=request.form.get("customers")
        invoice = Invoice(date=date,shift_id=shift_id,product=product,customer_id=customer_id,qty=qty,price=sales_price,vehicle_number=vehicle_number,driver_name=driver_name)
        db.session.add(invoice)
        db.session.commit()
        return redirect(url_for('ss26'))

@app.route("/sales_receipts",methods=["POST"])
@login_required
@start_shift_first
def sales_receipts():
        """Invoices for cash sales"""
        
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        date = current_shift.date
        shift_id = current_shift.id
        products = ["Petrol","Diesel"]
       
        account_id= int(request.form.get("account"))
        amount= float(request.form.get("amount"))
        while amount > 0:
                product = products[randint(0,1)]
                qty = receipt_product_qty(amount,shift_id,product)
                sales_price = get_product_price(shift_id,product)
                invoice = Invoice(date=date,product=product,shift_id=shift_id,customer_id=account_id,qty=qty,price=sales_price)
                db.session.add(invoice)
                db.session.commit()
                amount = amount-(qty*sales_price)
        return redirect(url_for('ss26'))

@app.route("/cash_up",methods=["POST"])
@login_required
@start_shift_first
def cash_up():
        """cash up"""
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_id = current_shift.id
        date = current_shift.date
        account = Customer.query.filter_by(name="Cash").first()
        expected_amount = request.form.get("expected_amount")#cash_sales_amt- cash exp
        actual_amount= request.form.get("actual_amount")
        variance= request.form.get("variance")
        amount= float(cash_sales_amount)
        products = ["Petrol","Diesel"]
        while amount > 0:
                product = products[randint(0,1)]
                qty = receipt_product_qty(amount,shift_id,product)
                sales_price = get_product_price(shift_id,product)
                invoice = Invoice(date=date,product=product,shift_id=shift_id,customer_id=account.id,qty=qty,price=sales_price)
                db.session.add(invoice)
                db.session.commit()
                amount = amount-(qty*sales_price)
        cash_up = CashUp(date=date,shift_id=shift_id,account_id=account.id,expected_amount=expected_amount,actual_amount=actual_amount,variance=variance)
        db.session.add(cash_up)
        db.session.commit()
        return redirect(url_for('ss26'))


