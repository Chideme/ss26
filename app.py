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
                shift_daytime = request.form.get("daytime")
                db.session.query(Shift_Underway).filter(Shift_Underway.id == 1).update({Shift_Underway.state: True}, synchronize_session = False)
                db.session.commit()
                shift = Shift(date=day,daytime=shift_daytime)
                db.session.add(shift)
                db.session.commit()
                flash('Shift Started')
                return redirect(url_for('readings_entry'))

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
@start_shift_first
def readings_entry():
        """Readings Entry"""
        pumps = Pump.query.all()
        tanks= Tank.query.all()
        products= Product.query.all()
        customers= Customer.query.all()
        accounts =Account.query.all()
        return render_template("readings_entry.html",tanks=tanks,pumps=pumps,products=products,customers=customers,accounts=accounts)

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

@app.route("/customer_sales",methods=["POST"])
@login_required
@start_shift_first
def customer_sales():
        """Sales Invoices"""
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        vehicle_number= request.form.get("vehicle_number")
        driver_name= request.form.get("driver_name")
        sales_price= request.form.get("sales_price")
        product = request.form.get("product")
        qty= request.form.get("qty")
        customer_id=request.form.get("customers")
        invoice = Invoice(date=date,shift_id=shift_id,product=product,customer_id=customer_id,qty=qty,price=sales_price,vehicle_number=vehicle_number,driver_name=driver_name)
        db.session.add(invoice)
        db.session.commit()
        return redirect(url_for('readings_entry'))

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
        price = Price.query.filter(and_(Price.shift_id == shift_id, Price.product_id == product_id))
        price = price.price
        account_id= request.form.get("account")
        amount= float(request.form.get("amount"))
        
        while amount:
                i = randint(0,1)
                qty = receipt_product_qty(amount,shift_id,products[i])
                invoice = Invoice(date=date,product=products[i],shift_id=shift_id,customer_id=account_id,qty=qty,price=sales_price)
                db.session.add(Invoice)
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

@app.route("/cash_up",methods=["POST"])
@login_required
@start_shift_first
def cash_up():
        """cash up"""
        current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        account = request.form.get("account")
        expected_amount= request.form.get("expected_amount")
        actual_amount= request.form.get("actual_amount")
        variance= request.form.get("variance")
        cash_up = CashUp(date=date,shift_id=shift_id,account=account,expected_amount=expected_amount,actual_amount=actual_amount,variance=variance)
        db.session.add(cash_up)
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
        user = User(username=request.form.get("username"),password=request.form.get("password"),role_id=request.form.get("role"))
        user_exists = bool(User.query.filter_by(username=request.form.get("username")).first())
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
        pump = Pump(name=request.form.get("pump_name"),tank_id=request.form.get("tank"))
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
        tank = Tank(name=request.form.get("tank_name"),product_id=request.form.get("product"))
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
        product = Product(name=request.form.get("product_name"),price=request.form.get("price"),product_type=request.form.get("product_type"))
        db.session.add(product)
        db.session.commit()
        flash("Product Added !!")
        return redirect(url_for('products'))

@app.route("/admin/delete_product",methods=["POST"])
@login_required
@admin_required
def delete_product():
        """Delete Product"""
        product = db.session.query(Tank).get(int(request.form.get("products")))
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
        customer = Customer(name=request.form.get("name"),phone_number=request.form.get("phone"),contact_person=request.form.get("contact_person"))
        customer_exists = bool(Customer.query.filter_by(name=request.form.get("name")).first())
        if customer_exists:
                flash("User already exists, Try using another username!!")
                return redirect(url_for('customers'))
        else:
                db.session.add(customer)
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
        account = Account(account_name=request.form.get("name"),account_category=request.form.get("category"))
        account_exists = bool(Account.query.filter_by(account_name=request.form.get("name")).first())
        if account_exists:
                flash("Account already exists, Try using another username!!")
                return redirect(url_for('accounts'))
        else:
                db.session.add(account)
                db.session.commit()
                flash('Account Successfully Added')
                return redirect(url_for('accounts'))




@app.route("/shift_driveway",methods=["GET","POST"])
def shift_driveway():
    """Query Shift Driveways for a particular day """
    if request.method == "POST":
        
            daytime= request.form.get("shift")
            shift_id = Shift.query.filter(and_(Shift.date == request.form.get("date"),Shift.daytime == daytime)).first()
            shift_id =shift_id.id
            prev_shift_id = int(shift_id)-1
            pump_readings = {}
            pumps = Pump.query.all()
            for pump in pumps:
                    prev_shift_reading = PumpReading.query.filter(and_(PumpReading.id == prev_shift_id,PumpReading.pump_id == pump.id)).first()
                    prev_shift_reading = prev_shift_reading.reading
                    current_shift_reading = PumpReading.query.filter(and_(PumpReading.id == shift_id,PumpReading.pump_id == pump.id)).first()
                    current_shift_reading = current_shift_reading.reading
                    pump_readings[pump.name]=[prev_shift_reading,current_shift_reading]
            tank_dips = {}
            tanks = Tank.query.all()
            for tank in tanks:
                    prev_shift_dip = TankDip.query.filter(and_(TankDip.id ==prev_shift_id,TankDip.tank_id == tank.id)).first()
                    prev_shift_dip = prev_shift_reading.dip
                    current_shift_dip= TankDip.query.filter(and_(TankDip.id ==shift_id,TankDip.tank_id == tank.id)).first()
                    current_shift_dip = current_shift_reading.reading
                    tank_dips[tank.name]=[prev_shift_dip,current_shift_dip]
            return render_template("ss26.html",tank_dips=tank_dips,pump_readings=pump_readings,pumps=pumps,tanks=tanks)
    else:
            return render_template("get_driveway.html")




