import os

from flask import Flask, session, render_template,flash,request,redirect,url_for,jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *
from models import *
from random import randint
from datetime import timedelta,datetime,date




# Set Database URL
#DATABASE_URL ="postgres://vyltpsivhqeaun:c0bb13175e810c1dcb143e03d1dc47b2ebaf46e095d9d6dfc8979d19f6a48e14@ec2-50-16-197-244.compute-1.amazonaws.com:5432/d3ud9s5a665gva"
DATABASE_URL ="postgres://localhost/ss26"
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["FLASK_ENV"] = os.getenv("FLASK_ENV")
app.secret_key = os.urandom(24)
db.init_app(app)

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
                        session["user"]= user.username
                        session["role_id"] = user.role_id
                        return redirect(url_for('get_driveway'))
        else:
                return render_template("login.html")

@app.route("/logout",methods=["GET"])
def logout():
        """Logs out User"""
        session.clear()
        
        return render_template("login.html")

@app.route("/dashboard/<heading>",methods=["GET","POST"])
@login_required
def dashboard(heading):
    """ Dashboard for Sales and Profit, to choose either, it is defined in the heading"""
    h = heading
    return render_template("dashboard.html",h=heading)


@app.route("/dashboard/reports",methods=["POST"])
@login_required
def dashboard_reports():
        """ Returns JSON Dashboard Reports"""
        heading = request.form.get("heading") #check whether the report is for profit or sales
        product = request.form.get("product")
        frequency = request.form.get("frequency")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        start_date = datetime.strptime(start_date,"%Y-%m-%d")
        end_date = datetime.strptime(end_date,"%Y-%m-%d")
        
        if frequency == "Day-to-day":
                if product=="Fuel":
                        if heading == "Sales":
                                data = fuel_daily_sales(start_date,end_date)
                                data ={str(i): data[i] for i in data} if data else "No data"
                                report = data
                        else:
                                data = fuel_daily_profit_report(start_date,end_date)
                                data ={str(i): data[i] for i in data} if data else "No data"
                                report = data
                else:
                        data =lubes_daily_sales(start_date,end_date)
                        data ={str(i): data[i] for i in data} if data else "No data"
                        report = data

        if frequency == "Month-to-month":
                if product =="Fuel":
                        if heading == "Sales":
                                data = fuel_mnth_sales(start_date,end_date)
                                data = {str(i): data[i] for i in data} if data else "No data"
                                report = data
                        else:
                                data = fuel_mnth_profit_report(start_date,end_date)
                                data ={str(i): data[i] for i in data} if data else "No data"
                                report = data
                else:
                        report = jsonify(lubes_mnth_sales(start_date,end_date))
        return report

@app.route("/dashboard/tank_variance",methods=["POST","GET"])
@login_required
def dashboard_tank_variance():
        """ Returns JSON Dashboard Reports"""
        
        tanks = Tank.query.all()
        return render_template("dashboard_tank_variances.html",tanks=tanks)


@app.route("/dashboard/variance",methods=["POST"])
@login_required
def dashboard_variance():
        """ Returns JSON Dashboard Reports"""
        
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        start_date = datetime.strptime(start_date,"%Y-%m-%d")
        end_date = datetime.strptime(end_date,"%Y-%m-%d")
        tank_id = int(request.form.get("tank"))
        report = get_tank_variance(start_date,end_date,tank_id)
        return report

        



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
                lubes = LubeProduct.query.all()
                if  pumps and  tanks:
                        shift_underway = Shift_Underway.query.get(1)
                        shift_underway.state = True
                        db.session.commit()
                        shift = Shift(date=day,daytime=shift_daytime)
                        db.session.add(shift)
                        db.session.commit()
                        ####
                        s = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                        current_shift = s[0]
                        prev_shift = s[1]
                        ####
                        
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        date = current_shift.date
                        prev_shift_id = prev_shift.id
        
                        if lubes:
                                for product in lubes:
                                        prev = LubeQty.query.filter(and_(LubeQty.shift_id==prev_shift_id,LubeQty.product_id==product.id)).first()
                                        prev_qty = prev.qty
                                        qty = LubeQty(shift_id=shift_id,date=date,qty=prev_qty,delivery_qty=prev.delivery_qty,product_id=product.id)
                                        db.session.add(qty)
                                        db.session.commit()
                        for pump in pumps:
                                product = db.session.query(Tank,Product,Pump).filter(and_(Tank.product_id == Product.id,Tank.id==Pump.tank_id,Pump.id == pump.id)).first()
                                product_id = product[1].id
                                prev_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev_shift_id,PumpReading.pump_id==pump.id)).first()
                                pump_readings =PumpReading(date=date,product_id=product_id,litre_reading=prev_reading.litre_reading,money_reading=prev_reading.money_reading,pump_id=pump.id,shift_id=shift_id)
                                db.session.add(pump_readings)
                                db.session.commit()
                        for tank in tanks:
                                prev_dip = TankDip.query.filter(and_(TankDip.shift_id==prev_shift_id,TankDip.tank_id==tank.id)).first()
                                tank_dip = TankDip(date=date,dip=prev_dip.dip,tank_id=tank.id,shift_id=shift_id)
                                db.session.add(tank_dip)
                                product = db.session.query(Tank,Product).filter(and_(Tank.product_id == Product.id,Tank.id == tank_id)).first()

                                product_id = product[1].id
                                fuel_delivery = Fuel_Delivery(date=date,shift_id=shift_id,tank_id=tank.id,qty=0,product_id=product_id,document_number='0000')
                                db.session.add(fuel_delivery)
                                db.session.commit()
                        
                        prev_prices = db.session.query(Product,Price).filter(and_(Product.id == Price.product_id,Price.shift_id == prev_shift_id)).all()
                        for i in prev_prices:
                                price = Price(date=date,shift_id=shift_id,product_id=i[0].id,cost_price=i[1].cost_price,selling_price=i[1].selling_price)
                                db.session.add(price)
                                db.session.commit()
                        shift_underway = Shift_Underway.query.get(1)
                        shift_underway.current_shift = shift_id
                        db.session.commit()
                        flash('Shift Started')
                        return redirect(url_for('ss26'))

                #Unfinished set up of products              
                else:
                        flash("Please finish set up")
                        return redirect(url_for('products'))

                                
        # Request is GET
        else:
                return render_template("start_shift_update.html")

@app.route("/end_shift_update",methods=["POST"])
@login_required
@start_shift_first
def end_shift_update():
        "End Update of Shift Figures"
        # first check if cash up on lubes has been done
        shift_underway = Shift_Underway.query.get(1)
        lubes = LubeProduct.query.all()
        check_cash_up = LubesCashUp.query.filter_by(shift_id=shift_id).first()
        if lubes:
                if check_cash_up:
                        shift_underway.state = False
                        db.session.commit()
                        flash('Shift Ended')
                        return redirect(url_for('get_driveway'))
                else:
                        flash('Do cash up on lubes')
                        return redirect(url_for('shift_lube_sales'))
        else:
                flash('Shift Ended')
                return redirect(url_for('get_driveway'))

        

@app.route("/driveway/edit",methods=["GET","POST"])
@login_required
def readings_entry():
        """Edit previous driveways"""
        pumps = Pump.query.all()
        tanks= Tank.query.all()
        products= Product.query.all()
        customers= Customer.query.all()
        cash_customers = Customer.query.filter_by(account_type="Cash")
        accounts =Account.query.all()
        lubes = LubeProduct.query.all()
        return render_template("readings_entry.html",lubes=lubes,tanks=tanks,pumps=pumps,products=products,customers=customers,accounts=accounts,cash_customers=cash_customers)

@app.route("/driveway/edit/price_change",methods=["GET","POST"])
@login_required
@admin_required
def price_change():
        """ Edit Price Change Outside shift update"""
        
        shift_id = int(request.form.get("shift"))
        cost_price = request.form.get("cost_price")
        selling_price = request.form.get("selling_price")
        product= Product.query.filter_by(id=request.form.get("product")).first()
        cost_price = request.form.get("cost_price")
        price = Price.query.filter(and_(Price.shift_id==shift_id,Price.product_id==product.id)).first()
        price.cost_price = cost_price
        price.selling_price= selling_price
        db.session.commit()
        return redirect(url_for('readings_entry'))

@app.route("/driveway/edit/pump_readings_entry",methods=["GET","POST"])
@login_required
@admin_required
def pump_readings_entry():
        """Edit readings for pumps """
        
        shift_id = int(request.form.get("shift"))
        pump_id= request.form.get("pump_name")
        litre_reading = request.form.get("litre_reading")
        money_reading = request.form.get("money_reading")
        reading = PumpReading.query.filter(and_(PumpReading.shift_id==shift_id,PumpReading.pump_id==pump_id)).first()
        reading.money_reading = money_reading
        reading.litre_reading = litre_reading
        db.session.commit()

        
        return redirect(url_for('readings_entry'))


@app.route("/driveway/edit/tank_dips_entry",methods=["POST"])
@login_required
@admin_required
def tank_dips_entry():
        """Edit Dips for Tanks """
        
        shift_id = int(request.form.get("shift"))
        tank_id = request.form.get("tank_name")
        tank_dip = request.form.get("tank_dip")
        tank = TankDip.query.filter(and_(TankDip.tank_id==tank_id,TankDip.shift_id==shift_id)).first()
        tank.dip = tank_dip
        #db.session.query(TankDip).filter(and_(TankDip.tank_id == tank_id,TankDip.shift_id ==shift_id)).update({TankDip.dip: tank_dip}, synchronize_session = False)
        db.session.commit()
        return redirect(url_for('readings_entry'))


@app.route("/driveway/edit/fuel_delivery",methods=["POST"])
@login_required
@admin_required
def fuel_delivery():
        """Edit  Fuel Deliveries"""   
        shift_id = int(request.form.get("shift"))
        tank_id= request.form.get("tank_name")
        delivery =request.form.get("litres_delivered")
        fuel_delivery = Fuel_Delivery.query.filter(and_(Fuel_Delivery.tank_id==tank_id,Fuel_Delivery.shift_id==shift_id)).first()
        #db.session.query(Fuel_Delivery).filter(and_(Fuel_Delivery.tank_id == tank_id,Fuel_Delivery.shift_id ==shift_id)).update({Fuel_Delivery.qty: delivery}, synchronize_session = False)
        db.session.commit()
        return redirect(url_for('readings_entry'))

@app.route("/driveway/edit/update_customer_sales",methods=["POST"])
@login_required
@admin_required
def update_customer_sales():
        """Sales Invoices"""
        inv = int(request.form.get("invoice"))
        current_shift = request.form.get("shift")
        shift_id = int(current_shift)
        vehicle_number= request.form.get("vehicle_number").capitalize()
        driver_name= request.form.get("driver_name").capitalize()
        sales_price= float(request.form.get("sales_price"))
        product_id = int(request.form.get("product"))
        qty= request.form.get("qty")
        customer_id=request.form.get("customers")
        invoice = Invoice.query.get(inv)
        invoice.vehicle_number = vehicle_number
        invoice.driver_name = driver_name
        invoice.price = sales_price
        invoice.product_id = product_id
        invoice.qty = qty
        db.session.commit()
        return redirect(url_for('readings_entry'))

@app.route("/driveway/edit/update_sales_receipts",methods=["POST"])
@login_required
@admin_required
def update_sales_receipts():
        """Invoices for cash sales"""
        
        shift_id = int(request.form.get("shift"))
        current_shift = Shift.query.get(shift_id)
        date = current_shift.date
        customer_id= int(request.form.get("account"))
        customer = Customer.query.get(customer_id).first()
        account = Account.query.filter_by(account_name==customer.name).first()
        amount= float(request.form.get("amount"))
        invoices = Invoice.query.filter(and_(Invoice.shift_id ==shift_id,Invoice.customer_id==customer_id)).all()
        receipt = SaleReceipt.query.filter(and_(SaleReceipt.shift_id==shift_id,SaleReceipt.account_id==account.id)).first()
        receipt.amount = amount
        #delete previous invoices to start afresh
        for invoice in invoices:
                db.session.delete(invoice)
        db.commit()

        cash_invoices = cash_sales(amount,customer_id,shift_id,date)# add invoices to cash customer account
        if cash_invoices:
                db.session.commit()

        
        return redirect(url_for('readings_entry'))


@app.route("/company_information/users",methods=["GET","POST"])
@login_required
@admin_required
def manage_users():
        """Managing Users"""
        if request.method == "GET":
                users_roles = db.session.query(User,Role).filter(Role.id == User.role_id).all()
                users= User.query.all()
                roles = Role.query.all()
                return render_template("manageusers.html",roles=roles,users_roles=users_roles,users=users)



@app.route("/company_information/users/add_user",methods=["POST"])
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

@app.route("/company_information/users//edit_user",methods=["POST"])
@login_required
@admin_required
def edit_user():
        """Edit User Information"""
        db.session.query(User).filter(User.username == request.form.get("username")).update({User.password: generate_password_hash(request.form.get("password"))}, synchronize_session = False)
        db.session.query(User).filter(User.username == request.form.get("username")).update({User.role_id: request.form.get("role")}, synchronize_session = False)
        db.session.commit()
        flash('User Successfully Updated')
        return redirect(url_for('manage_users'))

@app.route("/company_information/users//delete_user",methods=["POST"])
@login_required
@admin_required
def delete_user():
        """Deletes Users"""
        user = db.session.query(User).get(int(request.form.get("users")))
        db.session.delete(user)  
        db.session.commit()
        flash('User Successfully Removed!!')
        return redirect(url_for('manage_users'))



@app.route("/inventory/pumps/",methods=["GET","POST"])
@login_required
@admin_required
def pumps():
        """Pump List"""
        pump_tank = db.session.query(Tank,Pump).filter(Tank.id == Pump.tank_id).all()
        pumps =  Pump.query.all()
        tanks = Tank.query.all()
        return render_template("pumps.html",pumps=pumps,pump_tank=pump_tank,tanks=tanks)
        

@app.route("/inventory/pumps/add_pump",methods=["POST"])
@login_required
@admin_required
def add_pump():

        """Add Pump"""
        shift_underway = Shift_Underway.query.get(1)
        ######
        s = Shift.query.order_by(Shift.id.desc()).limit(2).all()
        current_shift = s[0]
        prev_shift = s[1]
        #check if there is a current shift going on and make the update to the correct previous shift
        if shift_underway.state == True:
                current_shift_id = current_shift.id
                prev_shift_id = prev_shift.id
                update_shift_id = current_shift.id
                update_shift = Shift.query.get(update_shift_id)
                name=request.form.get("pump_name").capitalize()
                tank_id=request.form.get("tank")
                litre_reading = request.form.get("litre_reading") # opening readings
                money_reading = request.form.get("money_reading")
                pump = Pump(name=name,tank_id=tank_id)
                try:
                        db.session.add(pump)
                        db.session.commit()
                except:
                        flash("There was an error adding pump to database")
                        return redirect(url_for('pumps'))
                
                else:
                        pump = Pump.query.filter_by(name=name).first()
                        product = db.session.query(Tank,Product,Pump).filter(and_(Tank.product_id == Product.id,Tank.id==Pump.tank_id,Tank.id == tank_id,Pump.id == pump.id)).first()
                        product_id = product[1].id
                        
                        try:
                                #reading1
                                open_readings1 = PumpReading(date=prev_shift.date,product_id=product_id,litre_reading=litre_reading,money_reading=money_reading,pump_id=pump.id,shift_id=prev_shift_id)
                                db.session.add(open_readings1)
                                #reading2
                                open_readings2 = PumpReading(date=current_shift.date,product_id=product_id,litre_reading=litre_reading,money_reading=money_reading,pump_id=pump.id,shift_id=current_shift_id)
                                db.session.add(open_readings2)
                                db.session.commit()
                        except:
                                db.session.delete(pump)
                                db.session.commit()
                                flash("There was an error adding pump to database")
                                return redirect(url_for('pumps'))
                
                
                        else:
                                flash('Pump Successfully Added !!')
                                return redirect(url_for('pumps'))

        else:
                
                name=request.form.get("pump_name").capitalize()
                tank_id=request.form.get("tank")
                litre_reading = request.form.get("litre_reading") # opening readings
                money_reading = request.form.get("money_reading")
                pump = Pump(name=name,tank_id=tank_id)
                try:
                        db.session.add(pump)
                        db.session.commit()
                except:
                        flash("There was an error adding pump to database")
                        return redirect(url_for('pumps'))
                
                else:
                        pump = Pump.query.filter_by(name=name).first()
                        product = db.session.query(Tank,Product,Pump).filter(and_(Tank.product_id == Product.id,Tank.id==Pump.tank_id,Tank.id == tank_id,Pump.id == pump.id)).first()
                        product_id = product[1].id
                        try:

                                open_readings = PumpReading(date=date,product_id=product_id,litre_reading=litre_reading,money_reading=money_reading,pump_id=pump.id,shift_id=current_shift.id)
                                db.session.add(open_readings)
                                db.session.commit()
                        except:
                                flash("There was an error adding pump to database")
                                return redirect(url_for('pumps'))
                        
                        
                        else:
                                flash('Pump Successfully Added !!')
                                return redirect(url_for('pumps'))


@app.route("/inventory/pumps/delete_pump",methods=["POST"])
@login_required
@admin_required
def delete_pump():
        """Delete Pump"""
        pump = db.session.query(Pump).get(int(request.form.get("pumps")))
        reading_record = PumpReading.query.filter_by(pump_id=pump.id).all()
        if reading_record:
                flash("Can not delete record !!")
                return redirect(url_for('pumps'))
        else:
                db.session.delete(pump)   
                db.session.commit()
                flash('Pump Successfully Removed!!')
                return redirect(url_for('pumps'))

@app.route("/inventory/tanks/add_tank",methods=["POST"])
@login_required
@admin_required
def add_tank():
        """Add Tank"""
        shift_underway = Shift_Underway.query.get(1)
        name =request.form.get("tank_name").capitalize()
        product_id=request.form.get("product")
        dip = request.form.get("dip")
        s = Shift.query.order_by(Shift.id.desc()).limit(2).all()
        current_shift = s[0]
        prev_shift = s[1]
        #check if there is a current shift going on and make the update to the correct previous shift
        if shift_underway.state == True:
                current_shift_id = current_shift.id
                prev_shift_id = prev_shift.id

                tank = Tank(name=name,product_id=product_id)
                try:
                        db.session.add(tank)
                        
                except:
                        flash("There was a problem whilst adding tank")
                        return redirect(url_for('tanks'))
                db.session.commit()
                tank = Tank.query.filter_by(name=name).first()
                try:
                        #reading1
                        open_dip1 = TankDip(date=prev_shift.date,shift_id=prev_shift_id,dip=dip,tank_id=tank.id,)
                        db.session.add(open_dip1)
                        #reading2
                        open_dip2 = TankDip(date=current_shift.date,shift_id=current_shift_id,dip=dip,tank_id=tank.id,)
                        db.session.add(open_dip2)
                        db.session.commit()
                except:
                        db.session.delete(tank)
                        db.session.commit()
                        flash("There was a problem whilst adding tank")
                        return redirect(url_for('tanks'))
                else:
                        flash("Tank Added Successfully !!")
                        return redirect(url_for('tanks'))
        else:
                current_shift_id = current_shift.id
                tank = Tank(name=name,product_id=product_id)
                try:
                        
                        db.session.add(tank)
                        
                except:
                        db.session.delete(tank)
                        db.session.commit()
                        flash("There was a problem whilst adding tank")
                        return redirect(url_for('tanks'))
                else:
                        db.session.commit()
                        tank = Tank.query.filter_by(name=name).first()
                try:
                        #reading2
                        open_dip2 = TankDip(date=current_shift.date,shift_id=current_shift_id,dip=dip,tank_id=tank.id,)
                        db.session.add(open_dip2)
                        db.session.commit()
                except:
                        db.session.delete(tank)
                        db.session.commit()
                        flash("There was a problem whilst adding tank")
                        return redirect(url_for('tanks'))
                else:
                        flash("Tank Added Successfully !!")
                        return redirect(url_for('tanks'))


@app.route("/inventory/tanks/delete_tank",methods=["POST"])
@login_required
@admin_required
def delete_tank():
        """Delete Tank"""
        tank = db.session.query(Tank).get(int(request.form.get("tanks")))
        pump_record = Pump.query.filter_by(tank_id=int(request.form.get("tanks"))).all()
        if pump_record:
                flash("Can not Delete Record")
                return redirect(url_for('tanks'))
        else:
                db.session.delete(tank)    
                db.session.commit()
                flash('Tank Successfully Removed!!')
                return redirect(url_for('tanks'))

@app.route("/inventory/tanks/",methods=["GET","POST"])
@login_required
@admin_required
def tanks():
        """Tank List"""
        tank_product = db.session.query(Tank,Product).filter(Product.id == Tank.product_id).all()
        tanks = Tank.query.all()
        products = Product.query.all()
        return render_template("tanks.html",tanks=tanks,products=products,tank_product=tank_product)

@app.route("/inventory/fuel_products/",methods=["GET","POST"])
@login_required
@admin_required
def products():
        """Product List"""
        products = Product.query.all()
        return render_template("products.html",products=products)

@app.route("/inventory/fuel_products/add_product",methods=["POST"])
@login_required
@admin_required
def add_product():
        """Add Product"""
        try:
                product = Product(name=request.form.get("product_name").capitalize(),price=request.form.get("price"),product_type=request.form.get("product_type"))
                db.session.add(product)
        except Exception as e:
                flash(e)
                return redirect(url_for('products'))
        
        else:
                db.session.commit()
                flash("Product Added !!")
                return redirect(url_for('products'))


@app.route("/inventory/fuel_products/delete_product",methods=["POST"])
@login_required
@admin_required
def delete_product():
        """Delete Product"""
        product = db.session.query(Product).get(int(request.form.get("products")))
        reading_entry = PumpReading.query.filter_by(product_id=int(request.form.get("products"))).all()
        if reading_entry:
                flash("Can not delete Record")
                return redirect(url_for('products'))
        else:
                db.session.delete(product)   
                db.session.commit()
                flash('Product Successfully Removed!!')
                return redirect(url_for('products'))


@app.route("/inventory/lubes/",methods=["GET","POST"])
@login_required
@admin_required
def lube_products():
        """Lubes Product List"""
        shift = Shift.query.order_by(Shift.id.desc()).first()
        products = LubeProduct.query.all()
        return render_template("lube_products.html",products=products,shift=shift)

@app.route("/inventory/lubes/add_lube_product/",methods=["POST"])
@login_required
@admin_required
def add_lube_product():
        """Add Product"""
        shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        #####
        s = Shift.query.order_by(Shift.id.desc()).limit(2).all()
        current_shift = s[0]
        prev_shift = s[1]
        #check if there is a current shift going on and make the update to the correct previous shift
        if shift_underway.state == True:
                update_shift_id = current_shift.id 
                prev_shift_id =   prev_shift.id
                name=request.form.get("product_name")
                cost_price=request.form.get("cost_price")
                selling_price=request.form.get("selling_price")
                mls=request.form.get("mls")
                open_qty = request.form.get("open_qty")
                product = LubeProduct(name=name,cost_price=cost_price,selling_price=selling_price,mls=mls)
                try:
                        db.session.add(product)
                        db.session.commit()
                except:
                        flash("There was an error adding product to database")
                        return redirect(url_for('lube_products'))
                else:
                
                        product = LubeProduct.query.filter_by(name=name).first()
                        try:
                        # add opening qty 
                                qty1 = LubeQty(shift_id = prev_shift.id,date=prev_shift.date,qty=open_qty,delivery_qty=0,product_id=product.id)
                                db.session.add(qty1)
                                # add closing qty 
                                qty2 = LubeQty(shift_id = current_shift.id,date=current_shift.date,qty=open_qty,delivery_qty=0,product_id=product.id)
                                db.session.add(qty2)
                        except Exception as e:
                                flash(e)
                                return redirect(url_for('lube_products'))
                        else:
                                db.session.commit()

                                flash("Product Added !!")
                                return redirect(url_for('lube_products')) 
        else:
                update_shift_id = current_shift.id

                update_shift = Shift.query.get(update_shift_id)
                name=request.form.get("product_name")
                cost_price=request.form.get("cost_price")
                selling_price=request.form.get("selling_price")
                mls=request.form.get("mls")
                open_qty = request.form.get("open_qty")
                product = LubeProduct(name=name,cost_price=cost_price,selling_price=selling_price,mls=mls)
                try:
                        db.session.add(product)
                        db.session.commit()
                except Exception as e:
                        flash(e)
                        return redirect(url_for('lube_products'))
                
                else:
                        product = LubeProduct.query.filter_by(name=name).first()
                        try:

                                qty = LubeQty(shift_id = update_shift.id,date=update_shift.date,qty=open_qty,delivery_qty=0,product_id=product.id)
                                db.session.add(qty)
                        except Exception as e:
                                flash(e)
                                return redirect(url_for('lube_products'))
                        else:
                                db.session.commit()

                                flash("Product Added !!")
                                return redirect(url_for('lube_products'))


@app.route("/inventory/lubes/delete_lube_product/",methods=["POST"])
@login_required
@admin_required
def delete_lube_product():
        """Delete Product"""

        product = db.session.query(Product).get(int(request.form.get("products")))
        try:
                db.session.delete(product)   
                db.session.commit()
        except Exception as e:
                flash(e)
                return redirect(url_for('lube_products'))
        else:
                flash('Product Successfully Removed!!')
                return redirect(url_for('lube_products'))


@app.route("/inventory/coupons/",methods=["GET","POST"])
@login_required
@admin_required
def coupons():
        """Coupon List"""
        coupons = Coupon.query.all()
        return render_template("coupons.html",coupons=coupons)

@app.route("/inventory/coupons/add_coupon",methods=["POST"])
@login_required
@admin_required
def add_coupon():
        """Add Coupons"""
        coupon = Coupon(name=request.form.get("coupon_name").capitalize(),coupon_qty=request.form.get("coupon_qty"))
        try:
                db.session.add(coupon)
        except:
                flash("Can not add record")
                return redirect(url_for('coupons'))
        else:
                db.session.commit()
                flash("Coupon Added !!")
                return redirect(url_for('coupons'))


@app.route("/inventory/coupons/delete_coupon",methods=["POST"])
@login_required
@admin_required
def delete_coupon():
        """Delete Coupon"""
        coupon = Coupon.query.get(request.form.get("coupon_id"))
        try:
                db.session.delete(coupon)
        except:
                flash('Can not delete record')
                return redirect(url_for('coupons'))
        else:
                db.session.commit()
                flash('Coupon Successfully Removed!!')
                return redirect(url_for('coupons'))

@app.route("/customers",methods=["GET","POST"])
@login_required
def customers():
        """Managing Customers"""
        customers= Customer.query.all()
        # calculate balances
        balances = {}
        for customer in customers:
                invoices = Invoice.query.filter_by(customer_id=customer.id).all()
                payments = CustomerPayments.query.filter_by(customer_id=customer.id).all()
                net = sum([i.amount for i in payments]) - sum([i.price*i.qty for i in invoices])
                balances[customer]=net
        return render_template("customers.html",customers=customers,balances=balances)

@app.route("/customers/customer_payment",methods=["POST"])
@login_required
@admin_required
def customer_payment():
        """Managing Customers"""
        date = request.form.get("date")
        customer_id = request.form.get("customers")
        amount = request.form.get("amount")
        ref = request.form.get("ref") or ""
        try:
                payment = CustomerPayments(date=date,customer_id=customer_id,amount=amount,ref=ref)
                db.session.add(payment)
        except:
                flash('There was error adding payment')
                return redirect(url_for('customers'))
        else:
                db.session.commit()
                flash('Payment Successfully Added')
                return redirect(url_for('customers'))

@app.route("/customers/<int:customer_id>",methods=["GET","POST"])
@login_required
def customer(customer_id):
        """Report for single customer"""
        customer = Customer.query.filter_by(id=customer_id).first()
        total_invoices = Invoice.query.filter_by(customer_id=customer_id).all()
        total_payments = CustomerPayments.query.filter_by(customer_id=customer_id).all()
        net = sum([i.amount for i in total_payments]) - sum([i.price*i.qty for i in total_invoices])
        #total_invoices = db.session.query(Invoice,Product).filter(and_(Invoice.product == str(Product.id),Invoice.customer_id==customer_id)).all()
        if request.method == "POST":
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                #invoices = Invoice.query.filter(and_(Invoice.customer_id==customer_id,Invoice.date.between(start_date,end_date))).all()
                invoices = db.session.query(Invoice,Product).filter(and_(Invoice.product_id == Product.id,Invoice.customer_id==customer_id,Invoice.date.between(start_date,end_date))).all()
                payments = CustomerPayments.query.filter(and_(CustomerPayments.customer_id==customer_id,CustomerPayments.date.between(start_date,end_date))).all()
                records = {}
                for i in invoices:
                        records[i[0].date] = {"inv":{},"pmnt":0,"bal":0}
                for i in payments:
                        if i.date in records:
                                pass
                        else:
                                records[i.date] = {"inv":{},"pmnt":0,"bal":0}
                for invoice in invoices:
                        records[invoice[0].date]["inv"][invoice[0].id] = [invoice[0].id,invoice[0].driver_name,invoice[0].vehicle_number,invoice[1].name,invoice[0].qty,invoice[0].price,
                        invoice[0].qty*invoice[0].price]
                        balance = sum([i.amount for i in total_payments if i.date <= invoice[0].date])-sum([i.price*i.qty for i in total_invoices if i.date <= invoice[0].date])
                        records[invoice[0].date]["bal"]= balance
                for payment in payments:
                        records[payment.date]["pmnt"]= records[payment.date]["pmnt"]+payment.amount
                        balance = sum([i.amount for i in total_payments if i.date <= payment.date])-sum([i.price*i.qty for i in total_invoices if i.date <= payment.date])
                        records[payment.date]["bal"]= balance
                dates = list(records)
                return render_template("customer.html",records=records,dates=dates,customer=customer,net=net,start=start_date,end=end_date)
        else:
                end_date = date.today()
                start_date = end_date - timedelta(days=900)
                #invoices = Invoice.query.filter(and_(Invoice.customer_id==customer_id,Invoice.date.between(start_date,end_date))).all()
                invoices = db.session.query(Invoice,Product).filter(and_(Invoice.product_id == Product.id,Invoice.customer_id==customer_id,Invoice.date.between(start_date,end_date))).all()
                payments = CustomerPayments.query.filter(and_(CustomerPayments.customer_id==customer_id,CustomerPayments.date.between(start_date,end_date))).all()
                records = {}
                inv_ids = {}
                for i in invoices:
                        records[i[0].date] = {"inv":{},"pmnt":0,"bal":0}
                        inv_ids[i[0].date] = []
                for i in payments:
                        if i.date in records:
                                pass
                        else:
                                records[i.date] = {"inv":{},"pmnt":0,"bal":0}
        
                for invoice in invoices:
                        balance = sum([i.amount for i in total_payments if i.date <= invoice[0].date])-sum([i.price*i.qty for i in total_invoices if i.id <= invoice[0].id ])
                        records[invoice[0].date]["inv"][invoice[0].id] = [invoice[0].id,invoice[0].driver_name,invoice[0].vehicle_number,invoice[1].name,invoice[0].qty,invoice[0].price,
                        invoice[0].qty*invoice[0].price,balance]
                        inv_ids[invoice[0].date].append(invoice[0].id)
                        
                        
                for payment in payments:
                        records[payment.date]["pmnt"]= records[payment.date]["pmnt"]+payment.amount
                        balance = sum([i.amount for i in total_payments if i.date <= payment.date])-sum([i.price*i.qty for i in total_invoices if i.date < payment.date])
                        records[payment.date]["bal"]= balance
                dates = sorted_dates(list(records))
                for i in inv_ids:
                        inv_ids[i]=sorted(inv_ids[i])

                return render_template("customer.html",records=records,inv_ids=inv_ids,dates=dates,customer=customer,net=net,start=start_date,end=end_date)

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
                        try:
                                db.session.add(customer)
                        except Exception as e:
                                flash(e)
                                return redirect(url_for('customers'))
                        else:
                                db.session.commit()
                                flash('Customer Successfully Added')
                                return redirect(url_for('customers'))
                else:
                        try:
                                db.session.add(customer)
                        except Exception as e:
                                flash(e)
                                return redirect(url_for('customers'))
                        else:
                                db.session.commit()
                        try:
                                account = Account(account_name=account_name,account_category=account_type)
                                db.session.add(account)
                        except Exception as e:
                                flash(e)
                                return redirect(url_for('customers'))
                        else:
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
        invoices = Invoice.query.filter_by(customer_id=customer.id).all()
        payments = CustomerPayments.query.filter_by(customer_id=customer.id).all()
        if invoices or payments:
                flash("Can not delete record")
                return redirect(url_for('customers'))
        else:
                db.session.delete(customer)   
                db.session.commit()
                flash('Customer Successfully Removed!!')
                return redirect(url_for('customers'))


@app.route("/suppliers/expenses/",methods=["GET","POST"])
@login_required
@admin_required
def accounts():
        """Managing Expense Accounts"""
        accounts= Account.query.filter_by(account_category="Expense").all()
        return render_template("accounts.html",accounts=accounts)

@app.route("/suppliers/expenses/delete_account",methods=["POST"])
@login_required
@admin_required
def delete_account():
        """Deletes Account"""
        account = db.session.query(Account).get(int(request.form.get("accounts")))
        try:
                db.session.delete(account)
        except Exception as e:
                flash(e)
                return redirect(url_for('accounts'))
        else:
                db.session.commit()
                flash('Account Successfully Removed!!')
                return redirect(url_for('accounts'))

@app.route("/suppliers/expenses/add_accounts",methods=["POST"])
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
                try:
                        db.session.add(account)
                except Exception as e:
                        flash(e)
                        return redirect(url_for('accounts'))
                else:
                        db.session.commit()
                        flash('Account Successfully Added')
                        return redirect(url_for('accounts'))

@app.route("/reports/cash_accounts",methods=["GET","POST"])
@login_required
@admin_required
def cash_accounts():
        """Cash Account Report"""
        accounts= Account.query.filter_by(account_category="Cash").all()
        balances= {}
        for account in accounts:
                receipts = SaleReceipt.query.filter_by(account_id=account.id).all()
                payouts = PayOut.query.filter_by(source_account=account.id).all()
                balance = sum([i.amount for i in receipts])- sum([i.amount for i in payouts])
                balances[account]=balance
        return render_template("cash_accounts.html",accounts=accounts,balances=balances)




@app.route("/reports/cash_accounts/<int:account_id>",methods=["GET","POST"])
@login_required
@admin_required
def cash_account(account_id):
        """Cash Account """
        account= Account.query.get(account_id)
        report= {}
        receipts = SaleReceipt.query.filter_by(account_id=account.id).all()
        payments = PayOut.query.filter_by(source_account=account.id).all()
        balances = sum([i.amount for i in receipts])- sum([i.amount for i in payments])
        for receipt in receipts:
                report[receipt.date]= {"rcpt":0,"pay":0,"bal":0}
                report[receipt.date]["rcpt"]=report[receipt.date]["rcpt"]+receipt.amount
                report[receipt.date]["bal"]= sum([i.amount for i in receipts if i.date <= receipt.date])-sum([i.amount for i in payments if i.date <= receipt.date])
        for payment in payments:
                if payment.date in report:
                        report[payment.date]["pay"]=report[payment.date]["pay"]+payment.amount
                else:
                        report[payment.date]={"rcpt":0,"pay":0,"bal":0}
                        report[payment.date]["bal"] = sum([i.amount for i in receipts if i.date <= payment.date])-sum([i.amount for i in payments if i.date <= payment.date])
        
        return render_template("cash_account.html",account=account,report=report,account_id=account_id,balances=balances)


@app.route("/reports/payouts/<date>/<cashaccount_id>",methods=["GET","POST"])
@login_required
@admin_required
def daily_payouts(date,cashaccount_id):
        """Expenses Report"""
        payouts = db.session.query(PayOut,Account).filter(PayOut.pay_out_account==Account.id,PayOut.date==date,PayOut.source_account==cashaccount_id).all()
        total = sum([i[0].amount for i in payouts])
        return render_template("daily_payouts.html",payouts=payouts,cashaccount_id=cashaccount_id,total=total,date=date)


@app.route("/reports/profit_statement",methods=["GET","POST"])
@login_required
@admin_required
def profit_statement():
        """ Gross Profit Statement as per shift"""
        products = Product.query.all()
        products = [product.name for product in products]
        if request.method =="GET":

                end_date = date.today()
                start_date = end_date - timedelta(days=900)
                report = fuel_product_profit_statement(start_date,end_date)

                return render_template("profit_statement.html",reports=report,start_date=start_date,end_date=end_date,products=products)
                
        else:
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                report = fuel_product_profit_statement(start_date,end_date)

                return render_template("profit_statement.html",reports=report,start_date=start_date,end_date=end_date,dates=dates,products=products)
                



@app.route("/reports/cashup",methods=["GET","POST"])
@login_required
@admin_required
def cash_up_reports():
        """Managing Cash Accounts"""
        if request.method =="GET":
                end_date = date.today()
                start_date =end_date-timedelta(days=60)
                cash = CashUp.query.filter(CashUp.date.between(start_date,end_date)).all()
                return render_template("cash_up_report.html",cash=cash,start_date=start_date,end_date=end_date)
        else:
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                cash = CashUp.query.filter(CashUp.date.between(start_date,end_date)).all()
                return render_template("cash_up_report.html",cash=cash,start_date=start_date,end_date=end_date)

@app.route("/reports/lubes_cashup",methods=["GET","POST"])
@login_required
@admin_required
def lubes_cash_up_reports():
        """Managing Cash Accounts"""
        if request.method =="GET":
                end_date = date.today()
                start_date =end_date-timedelta(days=60)
                cash = LubesCashUp.query.filter(CashUp.date.between(start_date,end_date)).all()
                return render_template("lubes_cash_up_report.html",cash=cash,start_date=start_date,end_date=end_date)
        else:
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                cash = LubesCashUp.query.filter(CashUp.date.between(start_date,end_date)).all()
                return render_template("lubes_cash_up_report.html",cash=cash,start_date=start_date,end_date=end_date)

@app.route("/reports/tank_variances/<int:tank_id>",methods=["GET","POST"])
@login_required
@admin_required
def tank_variances(tank_id):
        """Tank Variances Report"""
        tank = Tank.query.get(tank_id)
        if request.method =="GET":
                shift_underway = Shift_Underway.query.get(1)
                current_shift = shift_underway.current_shift
                current_shift = Shift.query.get(current_shift)
                end_date = current_shift.date
                start_date = end_date - timedelta(days=30)
                tank_dips = get_tank_variance(start_date,end_date,tank_id)

                return render_template("tank_variances.html",tank_dips=tank_dips,tank=tank)
        else:
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                start_date = check_first_date(start_date)

                tank_dips = get_tank_variance(start_date,end_date,tank_id)

                return render_template("tank_variances.html",tank_dips=tank_dips,tank=tank)
        


@app.route("/",methods=["GET","POST"])
@login_required
def get_driveway():

        """Query Shift Driveways for a particular day """
        if request.method == "POST":
                shift_daytime = request.form.get("shift")
                date = request.form.get("date")
                if shift_daytime != "Total":
                        current_shift= Shift.query.filter(and_(Shift.date == date,Shift.daytime == shift_daytime)).first()
                        shift_id = current_shift.id
                        #####
                        prev = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                        prev_shift_id=prev.id
                        ######
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
                                delivery = Fuel_Delivery.query.filter(and_(Fuel_Delivery.shift_id==shift_id,Fuel_Delivery.tank_id==tank.id)).all()
                                deliveries = sum([i.qty for i in delivery])
                                tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales,deliveries]
                        product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
                        cash_account = Customer.query.filter_by(name="Cash").first()
                        customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Invoice.customer_id != cash_account.id))
                        sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
                        total_sales_ltr= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
                        total_sales_amt= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1].selling_price for product in product_sales_ltr])
                        sales_breakdown["Cash"] = total_sales_amt- sum([sales_breakdown[i] for i in sales_breakdown])
                        expenses = db.session.query(PayOut,Account).filter(and_(PayOut.pay_out_account== Account.id,PayOut.shift_id==shift_id)).all()
                        total_cash_expenses = sum([i[0].amount for i in expenses])
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
                        
                        return render_template("get_driveway.html",avg_sales=avg_sales,mnth_sales=mnth_sales,lubes_daily_sale=lubes_daily_sale,
                        lubes_mnth_sales=lubes_mnth_sales,lube_avg=lube_avg,
                        products=products,accounts=accounts,cash_customers=cash_customers,customers=customers,
                        cash_up=cash_up,total_cash_expenses=total_cash_expenses,expenses=expenses,sales_breakdown=sales_breakdown,
                        shift_number=shift_id,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,
                        pumps=pumps,tanks=tanks,product_sales_ltr=product_sales_ltr,total_sales_ltr=total_sales_ltr,total_sales_amt=total_sales_amt)
                else:
                        #Driveway for the day
                        current_shift= Shift.query.filter_by(date=date).order_by(Shift.id.desc()).first()
                        shift_id = current_shift.id
                        prev_date = current_shift.date -timedelta(days=1)
                        prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
                        prev_shift_id = prev_shift.id
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
                                delivery = Fuel_Delivery.query.filter(and_(Fuel_Delivery.date==date,Fuel_Delivery.tank_id==tank.id)).all()
                                deliveries = sum([i.qty for i in delivery])
                                tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales,deliveries]
                        product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
                        cash_account = Customer.query.filter_by(name="Cash").first()
                        customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Invoice.customer_id != cash_account.id))
                        sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
                        total_sales_ltr= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
                        total_sales_amt= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1].selling_price for product in product_sales_ltr])
                        sales_breakdown["Cash"] = total_sales_amt- sum([sales_breakdown[i] for i in sales_breakdown])
                        expenses = db.session.query(PayOut,Account).filter(and_(PayOut.pay_out_account== Account.id,PayOut.date==date)).all()
                        total_cash_expenses = sum([i[0].amount for i in expenses])
                        cash_up = CashUp.query.filter_by(date=date).first()
                        products = Product.query.all()
                        customers = Customer.query.all()
                        cash_customers = Customer.query.filter_by(account_type="Cash")
                        accounts = Account.query.all()
                        suppliers = []#Supplier.query.all()
                        for i in suppliers:
                                accounts.append(i)
                        end_date = current_shift.date
                        avg_sales = fuel_sales_avg(get_month_day1(end_date),end_date)
                        daily_sales = fuel_daily_sales(get_month_day1(end_date),end_date) 
                        mnth_sales = sum([daily_sales[i] for i in daily_sales])
                        lubes_daily_sale = lubes_daily_sales(get_month_day1(end_date),end_date)
                        lubes_mnth_sales = sum([lubes_daily_sale[i] for i in lubes_daily_sale])
                        lube_avg = lubes_sales_avg(get_month_day1(end_date),end_date)
                        return render_template("get_driveway.html",avg_sales=avg_sales,mnth_sales=mnth_sales,lubes_daily_sale=lubes_daily_sale,
                        lubes_mnth_sales=lubes_mnth_sales,lube_avg=lube_avg,
                        products=products,accounts=accounts,cash_customers=cash_customers,customers=customers,
                        cash_up=cash_up,total_cash_expenses=total_cash_expenses,expenses=expenses,sales_breakdown=sales_breakdown,
                        shift_number="Total",date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,
                        pumps=pumps,tanks=tanks,total_sales_amt=total_sales_amt,total_sales_ltr=total_sales_ltr,product_sales_ltr=product_sales_ltr)        
                
        else:

                shift_underway = Shift_Underway.query.get(1)
                current_shift = shift_underway.current_shift
                current_shift = Shift.query.get(current_shift)
                #####
                shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                current_shift = shifts[0]
                prev_shift = shifts[1]
                if current_shift:
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        date = current_shift.date
                        prev_shift_id = prev_shift.id
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
                                delivery = Fuel_Delivery.query.filter(and_(Fuel_Delivery.shift_id==shift_id,Fuel_Delivery.tank_id==tank.id)).all()
                                deliveries = sum([i.qty for i in delivery])
                                tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales,deliveries]
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
                        total_lubes_shift_sales = lube_sales(shift_id,prev_shift_id)
                        total_lubes_shift_sales=sum([total_lubes_shift_sales[i][5]*total_lubes_shift_sales[i][2] for i in total_lubes_shift_sales])/1000
                        return render_template("get_driveway.html",avg_sales=avg_sales,mnth_sales=mnth_sales,lubes_daily_sale=lubes_daily_sale,
                        lubes_mnth_sales=lubes_mnth_sales,lube_avg=lube_avg,total_lubes_shift_sales=total_lubes_shift_sales,
                        products=products,accounts=accounts,cash_customers=cash_customers,customers=customers,
                        cash_up=cash_up,total_cash_expenses=total_cash_expenses,expenses=expenses,sales_breakdown=sales_breakdown,
                        shift_number=shift_id,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,
                        pumps=pumps,tanks=tanks,product_sales_ltr=product_sales_ltr,total_sales_amt=total_sales_amt,total_sales_ltr=total_sales_ltr)
                else:
                        flash("No shift updated yet")
                        return redirect('start_shift_update')
                        



@app.route("/ss26",methods=["GET"])
@login_required
@start_shift_first
def ss26():

        """UPDATE DRIVEWAY DATA """
               
        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        #######
        shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
        current_shift = shifts[0]
        prev_shift = shifts[1]
        if current_shift:
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                prev_shift_id = prev_shift.id
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
                        delivery = Fuel_Delivery.query.filter(and_(Fuel_Delivery.shift_id==shift_id,Fuel_Delivery.tank_id==tank.id)).all()
                        deliveries = sum([i.qty for i in delivery])
                        tank_dips[tank.name]=[prev_shift_dip,current_shift_dip,pump_sales,deliveries]
                product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
                cash_account = Customer.query.filter_by(name="Cash").first()
                customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Invoice.customer_id != cash_account.id))
                sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
                total_sales_ltr= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
                total_sales_amt= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1].selling_price for product in product_sales_ltr])
                sales_breakdown["Cash"] = total_sales_amt- sum([sales_breakdown[i] for i in sales_breakdown])
                expenses = db.session.query(PayOut,Account).filter(and_(PayOut.pay_out_account== Account.id,PayOut.shift_id==shift_id)).all()
                total_cash_expenses = sum([i[0].amount for i in expenses])
                cash_up = CashUp.query.filter_by(shift_id=shift_id).first()
                products = Product.query.all()
                coupons = Coupon.query.all()
                customers = Customer.query.all()
                cash_customers = Customer.query.filter_by(account_type="Cash")
                expense_accounts = Account.query.filter_by(account_category="Expense").all()
                cash_accounts = Account.query.filter_by(account_category="Cash").all()
                
                return render_template("ss26.html",
                products=products,expense_accounts=expense_accounts,cash_accounts=cash_accounts,
                cash_customers=cash_customers,customers=customers,coupons=coupons,
                cash_up=cash_up,total_cash_expenses=total_cash_expenses,expenses=expenses,sales_breakdown=sales_breakdown,
                shift_number=shift_id,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,
                pumps=pumps,tanks=tanks,product_sales_ltr=product_sales_ltr,total_sales_amt=total_sales_amt,total_sales_ltr=total_sales_ltr)
        else:
                flash("NO SHIFT STARTED YET")
                return redirect ('start_shift_update')





@app.route("/update_pump_litre_readings",methods=['POST'])
@login_required
@start_shift_first
def update_pump_litre_readings():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        pump = Pump.query.filter_by(name=request.form.get("pump")).first()
        pump_id = pump.id
        reading = request.form.get("litre_reading")
        db.session.query(PumpReading).filter(and_(PumpReading.pump_id == pump_id,PumpReading.shift_id== shift_id)).update({PumpReading.litre_reading: reading}, synchronize_session = False)
        db.session.commit()

        return redirect('ss26')

@app.route("/update_pump_money_readings",methods=['POST'])
@login_required
@start_shift_first
def update_pump_money_readings():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        pump = Pump.query.filter_by(name=request.form.get("pump")).first()# get pumpid
        pump_id = pump.id
        reading = request.form.get("money_reading")
        db.session.query(PumpReading).filter(and_(PumpReading.pump_id == pump_id,PumpReading.shift_id ==shift_id)).update({PumpReading.money_reading: reading}, synchronize_session = False)
        db.session.commit()

        return redirect('ss26')


@app.route("/update_tank_dips",methods=['POST'])
@login_required
@start_shift_first
def update_tank_dips():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        tank= Tank.query.filter_by(name=request.form.get("tank")).first()
        tank_id = tank.id
        tank_dip = request.form.get("tank_dip")
        db.session.query(TankDip).filter(and_(TankDip.tank_id == tank_id,TankDip.shift_id ==shift_id)).update({TankDip.dip: tank_dip}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_fuel_deliveries",methods=['POST'])
@login_required
@start_shift_first
def update_fuel_deliveries():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        tank= Tank.query.filter_by(name=request.form.get("tank")).first()
        tank_id = tank.id
        delivery = request.form.get("delivery")
        db.session.query(Fuel_Delivery).filter(and_(Fuel_Delivery.tank_id == tank_id,Fuel_Delivery.shift_id ==shift_id)).update({Fuel_Delivery.qty: delivery}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_cost_prices",methods=['POST'])
@login_required
@start_shift_first
def update_cost_prices():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        product= Product.query.filter_by(name=request.form.get("product")).first()
        cost_price = float(request.form.get("cost_price"))
        db.session.query(Price).filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).update({Price.cost_price: cost_price}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_selling_prices",methods=['POST'])
@login_required
@start_shift_first
def update_selling_prices():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_id = current_shift.id
        product= Product.query.filter_by(name=request.form.get("product")).first()
        selling_price = float(request.form.get("selling_price"))
        db.session.query(Price).filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).update({Price.selling_price: selling_price}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_shift_date",methods=['POST'])
@login_required
@start_shift_first
def update_shift_date():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_id = current_shift.id
        date = request.form.get("date")
        db.session.query(Shift).filter(Shift.id==shift_id).update({Shift.date: date}, synchronize_session = False)
        db.session.commit()
        return redirect('ss26')

@app.route("/update_shift_daytime",methods=['POST'])
@login_required
@start_shift_first
def update_shift_daytime():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
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
        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        vehicle_number= request.form.get("vehicle_number").capitalize()
        driver_name= request.form.get("driver_name").capitalize()
        sales_price= float(request.form.get("sales_price"))
        product_id = request.form.get("product")
        qty= request.form.get("qty")
        customer_id=request.form.get("customers")
        invoice = Invoice(date=date,shift_id=shift_id,product_id=product_id,customer_id=customer_id,qty=qty,price=sales_price,vehicle_number=vehicle_number,driver_name=driver_name)
        db.session.add(invoice)
        db.session.commit()
        return redirect(url_for('ss26'))

@app.route("/sales_receipts",methods=["POST"])
@login_required
@start_shift_first
def sales_receipts():
        """Invoices for cash sales"""
        
        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        date = current_shift.date
        shift_id = current_shift.id
        account= request.form.get("account")
        customer = Customer.query.filter_by(name=account).first()
        cash_account = Account.query.filter_by(name=account).first()
        amount= float(request.form.get("amount"))
        receipt = SaleReceipt(date=date,shift_id=shift_id,account_id=cash_account.id,amount=amount)
        db.session.add(receipt)
        db.session.commit()
        cash_invoices = cash_sales(amount,customer.id,shift_id,date)# add invoices to cash customer account
        if cash_invoices:
                db.session.commit()
                
                
        return redirect(url_for('ss26'))


@app.route("/coupon_sales",methods=["POST"])
@login_required
@start_shift_first
def coupon_sales():
        """Invoices for coupon sales"""
        
        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        date = current_shift.date
        shift_id = current_shift.id
        product = Product.query.get(request.form.get("product_id"))
        coupon = Coupon.query.get(request.form.get("coupon_id"))
        number_of_coupons = request.form.get("number_of_coupons")
        total_litres = int(coupon.coupon_qty) * int(number_of_coupons)
        customer = Customer.query.filter_by(name="Coupons").first()
        price = Price.query.filter(and_(Price.shift_id==shift_id,Price.product_id==product.id)).first()
        coupon_sale = CouponSale(date=date,shift_id=shift_id,product_id=product.id,coupon_id=coupon.id,qty=number_of_coupons)
        db.session.add(coupon_sale)
        db.session.commit()
        invoice = Invoice(date=date,product_id=product.id,shift_id=shift_id,customer_id=customer.id,qty=total_litres,price=price.selling_price)
        db.session.add(invoice)
        db.session.commit()
                
        return redirect(url_for('ss26'))


@app.route("/cash_up",methods=["POST"])
@login_required
@start_shift_first
def cash_up():
        """cash up"""
        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_id = current_shift.id
        date = current_shift.date
        account = Customer.query.filter_by(name="Cash").first()
        expected_amount = float(request.form.get("expected_amount"))
        cash_sales_amount = float(request.form.get("cash_sales_amount"))
        actual_amount= float(request.form.get("actual_amount"))
        variance= float(request.form.get("variance"))
        cash_account = Account.query.filter_by(account_name="Cash").first()
        amount= float(cash_sales_amount)
        cash_up = CashUp(date=date,shift_id=shift_id,sales_amount=cash_sales_amount,expected_amount=expected_amount,actual_amount=actual_amount,variance=variance)
        receipt = SaleReceipt(date=date,shift_id=shift_id,account_id=cash_account.id,amount=amount)
        db.session.add(cash_up)
        db.session.add(receipt)
        db.session.commit()
        cash_invoices = cash_sales(amount,account.id,shift_id,date)# add invoices to cash customer account
        if cash_invoices:
                db.session.commit()
        return redirect(url_for('ss26'))

@app.route("/payouts",methods=["POST"])
@login_required
@start_shift_first
def pay_outs():
        """payouts"""
        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        amount= request.form.get("amount")
        source_account= request.form.get("source_account")
        pay_out_account= request.form.get("pay_out_account")
        pay_out = PayOut(source_account=source_account,pay_out_account=pay_out_account,date=date,shift_id=shift_id,amount=amount)
        db.session.add(pay_out)
        db.session.commit()
        return redirect(url_for('ss26'))

@app.route("/admin/restart_shift",methods=["POST"])
@login_required
@admin_required
def restart_shift():
        """Restart Shift"""
        shift_id = request.form.get("shift")
        invoices = Invoice.query.filter_by(shift_id=shift_id).all()
        pay_outs = PayOut.query.filter_by(shift_id=shift_id).all()
        sales_receipts = SaleReceipt.query.filter_by(shift_id=shift_id).all()
        cash_ups = CashUp.query.filter_by(shift_id=shift_id).all()

        for invoice in invoices:
                db.session.delete(invoice)    
                db.session.commit()
        for pay_out in pay_outs:
                db.session.delete(pay_out)    
                db.session.commit()
        for sales_receipt in sales_receipts:
                db.session.delete(sales_receipt)    
                db.session.commit()
        for cash_up in cash_ups:
                db.session.delete(cash_up)    
                db.session.commit()

        
        shift_underway = Shift_Underway.query.get(1)
        shift_underway.current_shift = int(shift_id)
        db.session.commit()
        flash('Shift Restarted !!')
        return redirect(url_for('ss26'))

@app.route("/shift_lube_sales",methods=["POST","GET"])
@login_required
@start_shift_first
@lubes_cash_up
def shift_lube_sales():
        """LUBE SALES PER SHIFT"""
        shift_underway = Shift_Underway.query.get(1)
        ########
        shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
        current_shift = shifts[0]
        prev_shift = shifts[1]
        #######
        shift_id = current_shift.id
        date = current_shift.date
        daytime = current_shift.daytime
        prev_shift_id = prev_shift.id
        products = LubeProduct.query.all()
        product_sales = lube_sales(shift_id,prev_shift_id)               
        total_sales_amt = sum([product_sales[i][2]*product_sales[i][4] for i in product_sales])
        total_sales_ltrs = sum([product_sales[i][5]*product_sales[i][2] for i in product_sales])/1000
        
        return render_template("shift_lube_sales.html",product_sales=product_sales,shift_number=shift_id,
                                date=date,shift_daytime =daytime,total_sales_amt=total_sales_amt,total_sales_ltrs=total_sales_ltrs,products=products)


@app.route("/update_lube_qty",methods=['POST'])
@login_required
def update_lube_qty():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        req =request.form.get("shift_id")# if the update is from  editing a previous shift
        if req:
                current_shift = Shift.query.get(req)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                product = LubeProduct.query.filter_by(id=request.form.get("product")).first() 
                product_qty = LubeQty.query.filter(and_(LubeQty.shift_id==current_shift.id,LubeQty.product_id==product.id)).first()
                if product_qty:
                        try:
                                product_qty.qty = request.form.get("qty")
                        except Exception as e:
                                flash(e)
                                return redirect(url_for('readings_entry'))
                        else:
                                db.session.commit()
                                return redirect(url_for('readings_entry'))
                else:
                        qty =request.form.get("qty")
                        lube_qty = LubeQty(shift_id=shift_id,date=date,qty=qty,delivery_qty=0,product_id=product.id)
                        try:
                                db.session.add(lube_qty)
                        except Exception as e:
                                flash(e)
                                return redirect(url_for('readings_entry'))
                        else:
                                db.session.commit()
                                return redirect(url_for('readings_entry'))
        else:
                        
                shift_underway = Shift_Underway.query.get(1)
                current_shift = shift_underway.current_shift
                current_shift = Shift.query.get(current_shift)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                try:
                        product = LubeProduct.query.filter_by(id=request.form.get("product")).first() 
                        product = LubeQty.query.filter(and_(LubeQty.shift_id==current_shift.id,LubeQty.product_id==product.id)).first()
                        product.qty = request.form.get("qty")
                except Exception as e:
                        flash(e)
                        return redirect('shift_lube_sales')
                else:
                        db.session.commit()

                        return redirect('shift_lube_sales')

@app.route("/update_lubes_deliveries",methods=['POST'])
@login_required
def update_lubes_deliveries():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        req =request.form.get("shift_id")
        if req:
                current_shift = Shift.query.get(req)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                try:
                        product = LubeProduct.query.filter_by(name=request.form.get("product")).first() 
                        product = LubeQty.query.filter(and_(LubeQty.shift_id==current_shift.id,LubeQty.product_id==product.id)).first()
                        product.delivery_qty = request.form.get("qty")
                except Exception as e:
                        flash(e)
                        return redirect('readings_entry')
                else:
                        db.session.commit()
                        return redirect('readings_entry')
        else:
                        
                shift_underway = Shift_Underway.query.get(1)
                current_shift = shift_underway.current_shift
                current_shift = Shift.query.get(current_shift)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                try:
                        product = LubeProduct.query.filter_by(name=request.form.get("product")).first() 
                        product = LubeQty.query.filter(and_(LubeQty.shift_id==current_shift.id,LubeQty.product_id==product.id)).first()
                        product.delivery_qty = request.form.get("qty")
                except Exception as e:
                        flash(e)
                        return redirect('shift_lube_sales')
                else:
                        db.session.commit()
                        return redirect('shift_lube_sales')


@app.route("/update_lubes_cost_prices",methods=['POST'])
@login_required
def update_lubes_cost_prices():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        req =request.form.get("shift_id")
        if req:
                current_shift = Shift.query.get(req)
        else:
                        
                shift_underway = Shift_Underway.query.get(1)
                current_shift = shift_underway.current_shift
                current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        product = LubeProduct.query.filter_by(name=request.form.get("product")).first() 
        product.cost_price = request.form.get("cost_price")
        db.session.commit()
        return redirect('shift_lube_sales')

@app.route("/update_lubes_selling_prices",methods=['POST'])
@login_required
def update_lubes_selling_prices():

        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        req =request.form.get("shift_id")
        if req:
                current_shift = Shift.query.get(req)
        else:
                        
                shift_underway = Shift_Underway.query.get(1)
                current_shift = shift_underway.current_shift
                current_shift = Shift.query.get(current_shift)
        shift_daytime = current_shift.daytime
        shift_id = current_shift.id
        date = current_shift.date
        product = LubeProduct.query.filter_by(name=request.form.get("product")).first() 
        product.cost_price = request.form.get("selling_price")
        db.session.commit()
        return redirect('shift_lube_sales')

@app.route("/lubes_cash_up",methods=["POST"])
@login_required
@start_shift_first
@lubes_cash_up
def lubes_cash_up():
        """lubes cash up"""
        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        shift_underway = Shift_Underway.query.get(1)
        current_shift = shift_underway.current_shift
        current_shift = Shift.query.get(current_shift)
        shift_id = current_shift.id
        date = current_shift.date
        cash_sales_amount = request.form.get("cash_sales_amount") or 0
        cash_sales_amount = float(cash_sales_amount)
        expected_amount = float(request.form.get("expected_amount"))
        variance = cash_sales_amount-expected_amount
        check_cash_up = LubesCashUp.query.filter_by(shift_id=shift_id).first()
        cash_up = LubesCashUp(date=date,shift_id=shift_id,sales_amount=expected_amount,expected_amount=expected_amount,actual_amount=cash_sales_amount,variance=variance)
        
        try:
                db.session.add(cash_up)
        except Exception as e:
                flash(e)
                return redirect(url_for('shift_lube_sales'))

        else:
                db.session.commit()
                flash("Cash up for Lubricants done!!")
                return redirect(url_for('ss26'))