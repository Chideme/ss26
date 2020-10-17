import os

from flask import Flask, session, render_template,flash,request,redirect,url_for,jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from sqlalchemy import and_, or_,MetaData,Table
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *
from models import *
from random import randint
from datetime import timedelta,datetime,date



DATABASE_URL=os.getenv("DATABASE_URL")
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}  
app.config["FLASK_ENV"] = os.getenv("FLASK_ENV")
app.secret_key = os.urandom(24)
db.init_app(app)
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'kudakwashechideme@gmail.com',
    MAIL_PASSWORD = '@cee%kay',
))
mail = Mail(app)



@app.route("/",methods=["GET"])
def index():
        """App Landing page"""
        
        return render_template("index.html")

@app.route("/signup",methods=["GET","POST"])
def signup():
        """Tenant sign up page"""
        if request.method == "POST":
                company = request.form.get("tenant")
                address = request.form.get("address").capitalize()
                email = request.form.get("email").lower()
                contact_person = request.form.get("contact_person").capitalize()
                phone_number = request.form.get("phone")
                schema = create_schema_name(company.lower())
                tenant = Tenant(name =company.capitalize(),address=address,company_email=email,database_url=DATABASE_URL,tenant_code=schema,phone_number=phone_number,contact_person=contact_person,schema=schema,active=False)
                try:
                        db.session.add(tenant)
                        db.session.flush
                except:
                        flash("Account already created use login in page, or contact support")
                        return redirect(url_for('login'))
                try:
                
                        db.session.execute('CREATE SCHEMA IF NOT EXISTS {}'.format(schema))
                        db.session.commit()
                except:
                        flash("Account already created use login in page or contact support")
                        return redirect(url_for('login'))
                
                #####
                create_tenant_tables(schema)
                
                session['schema'] =tenant.schema
                session['tenant']= tenant.id
                
                return redirect(url_for('activate',tenant_schema=session['schema']))
                
        return render_template("signup.html")


@app.route("/<tenant_schema>/activate",methods=["GET","POST"])
def activate(tenant_schema):
        
        if request.method =="GET":
                

                return render_template("signup2.html")

        else:
                #db.session.create_all()
                
                with db.session.connection(execution_options={"schema_translate_map":{"tenant":tenant_schema}}):
                        #db.create_all()
                        #tenant = Tenant.query.filter_by(schema=tenant_schema).first()
                        super_user = "Admin"
                        password= get_random_string()
                        hash_password = generate_password_hash(password)
                        tenant_id = session['tenant']
                        tenant = Tenant.query.get(tenant_id)
                        user=User(username=super_user,password=hash_password,role_id=1,tenant_id=tenant_id,schema=session["schema"])
                        shift_underway = Shift_Underway(state=False,current_shift=0)
                        msg_body = "<h3>Please find your login details :</h3><body><p>Company Code: {}</p><p>User Name: Admin</p><p>Password: {}</p><small>Make sure to change your password once logged in</small></body>".format(tenant.id,password)
                        db.session.add(shift_underway)  
                        db.session.add(user)
                        db.session.flush()
                        tenant.active = True
                        session["user_id"] = user.id
                        session["user_tenant"]= user.tenant_id
                        session["role_id"] = user.role_id
                        session["shift_underway"]=False
                        msg = Message(subject="Welcome Admin!",
                                sender="kudakwashechideme@gmail.com",
                                recipients=[tenant.company_email],
                                html=msg_body)
                        try:
                                mail.send(msg)
                                db.session.commit()
                                flash('Account Successfully activated. Please use details sent to your email to login.')
                                return redirect(url_for('login'))
                                
                        except:  
                                db.session.commit()
                                flash('Account Successfully activated. Please use details sent to your email to login.')
                                return redirect(url_for('login'))




@app.route("/login",methods=["GET","POST"])
def login():
        """Log In Company session"""
        session.clear()

       #log in company id

        if request.method == "POST":
                tenant_id = request.form.get("tenant_id")
                company = Tenant.query.get(tenant_id)
                try:
                        active =  company.active

                except:
                        flash('Company does not exist, check your code and try again or contact support')
                        return render_template("login.html")

                if company:
                        if active:
                                session['tenant'] = company.id
                                session["schema"] = company.schema
                                return redirect(url_for('user_login'))

                        else:
                                session["schema"] = company.schema
                                session['tenant'] = company.id
                                flash('Company is not yet active. Please activate your company profile')
                                return redirect(url_for('activate',tenant_schema=session['schema']))
                        

                else:
                        flash('Company does not exist, check your code and try again or contact support')
                        return render_template("login.html")
        else:
                
                return render_template("login.html")


@app.route("/user_login",methods=["GET","POST"])
def user_login():
        """Log In User"""
        

       #check user login crenditials
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
       
                if request.method == "POST":
                        
                        
                        username = str(request.form.get("username"))
                        password = request.form.get("password")
                        user = User.query.filter_by(username=request.form.get("username")).first()
                        org = Tenant.query.get(session["tenant"])
                        shift_underway = Shift_Underway.query.all()
                        u = user.username
                        
                        if username != u or not check_password_hash(user.password,password) or session['tenant'] != user.tenant_id:
                                if org.active == False and User.query.filter_by(session["tenant"]).all() == None:

                                        flash("Please finish setting up your account")
                                        return redirect(url_for('activate',tenant_schema= org.schema))
                                else:     
                                        flash("Login details not correct,check your details and try again !!")
                                        return redirect(url_for('user_login'))
                        else:
                                session["user_id"] = user.id
                                session["user"] = user.username
                                session["user_tenant"]= user.tenant_id
                                session["role_id"] = user.role_id
                                session["shift_underway"] = shift_underway[0].state
                                session["org_name"]= org.name
                                
                                
                                return redirect(url_for('dashboard',heading='Sales'))
                else:
                        return render_template("login2.html")

@app.route("/logout",methods=["GET"])
@check_schema
def logout():
        """Logs out User"""
        session.clear()
        
        return render_template("login.html")

@app.route("/dashboard/<heading>",methods=["GET","POST"])
@login_required
@check_schema
def dashboard(heading):
    """ Dashboard for Sales and Profit, to choose either, it is defined in the heading"""
    with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
        end_date = date.today()

        start_date =  end_date- timedelta(days=360)
        h = heading
        if h == "Sales" or h =="Profit":
                return render_template("dashboard.html",h=heading,start_date=start_date,end_date=end_date)
        else:
                return render_template("404.html")


@app.route("/dashboard/reports",methods=["POST"])
@login_required
@check_schema
def dashboard_reports():
        """ Returns JSON Dashboard Reports"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
                                        sorted_date= sorted_dates([i for i in data])
                                        data_info = [data[i] for i in sorted_date]
                                        data_dates = [i.strftime('%d-%b-%y')  for i in sorted_date]
                                        report = jsonify({'Date':data_dates,'Data':data_info})
                                else:
                                        data = fuel_daily_profit_report(start_date,end_date)
                                        sorted_date= sorted_dates([i for i in data])
                                        data_info = [data[i] for i in sorted_date]
                                        data_dates = [i.strftime('%d-%b-%y')  for i in sorted_date]
                                        report = jsonify({'Date':data_dates,'Data':data_info})
                        else:
                                if heading == "Sales":
                                        data = lubes_daily_sales(start_date,end_date)
                                        sorted_date= sorted_dates([i for i in data])
                                        data_info = [data[i] for i in sorted_date]
                                        data_dates = [i.strftime('%d-%b-%y')  for i in sorted_date]
                                        report = jsonify({'Date':data_dates,'Data':data_info})
                                else:
                                        data = lubes_daily_profit_report(start_date,end_date)
                                        sorted_date= sorted_dates([i for i in data])
                                        data_info = [data[i] for i in sorted_date]
                                        data_dates = [i.strftime('%d-%b-%y')  for i in sorted_date]
                                        report = jsonify({'Date':data_dates,'Data':data_info})
                if frequency == "Month-to-month":
                        if product =="Fuel":
                                if heading == "Sales":
                                        data = fuel_mnth_sales(start_date,end_date)
                                        data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
                                        sorted_date= sorted_dates([i for i in data])
                                        data_info = [data[i] for i in sorted_date]
                                        data_dates = [i.strftime('%b-%y')  for i in sorted_date]
                                        report = jsonify({'Date':data_dates,'Data':data_info})
                                        
                                else:
                                        data = fuel_mnth_profit_report(start_date,end_date)
                                        data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
                                        sorted_date= sorted_dates([i for i in data])
                                        data_info = [data[i] for i in sorted_date]
                                        data_dates = [i.strftime('%b-%y')  for i in sorted_date]
                                        report = jsonify({'Date':data_dates,'Data':data_info})
                        else:
                                if heading == "Sales":
                                        data = lubes_mnth_sales(start_date,end_date)
                                        data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
                                        sorted_date= sorted_dates([i for i in data])
                                        data_info = [data[i] for i in sorted_date]
                                        data_dates = [i.strftime('%b-%y')  for i in sorted_date]
                                        report = jsonify({'Date':data_dates,'Data':data_info})
                                        
                                else:
                                        data = lubes_mnth_profit_report(start_date,end_date)
                                        data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
                                        sorted_date= sorted_dates([i for i in data])
                                        data_info = [data[i] for i in sorted_date]
                                        data_dates = [i.strftime('%b-%y')  for i in sorted_date]
                                        report = jsonify({'Date':data_dates,'Data':data_info})
                return report

@app.route("/dashboard/tank_variance",methods=["POST","GET"])
@login_required
@check_schema
def dashboard_tank_variance():
        """ Returns JSON Dashboard Reports"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                end_date = date.today()
                start_date =  end_date- timedelta(days=360)
                tanks = Tank.query.all()
                return render_template("dashboard_tank_variances.html",tanks=tanks,start_date=start_date,end_date=end_date)


@app.route("/dashboard/variance",methods=["POST"])
@login_required
@check_schema
def dashboard_variance():
        """ Returns JSON Dashboard Reports for tank variances"""

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
        
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                start_date = datetime.strptime(start_date,"%Y-%m-%d")
                end_date = datetime.strptime(end_date,"%Y-%m-%d")
                tank_id = int(request.form.get("tank"))
                data = tank_variance_daily_report(start_date,end_date,tank_id)
                sorted_date= sorted_dates([i for i in data])
                data_info = [data[i] for i in sorted_date]
                data_dates = [i.strftime('%d-%b-%y')  for i in sorted_date]
               
                

                return jsonify({'Date':data_dates,'Data':data_info})

        



@app.route("/driveway/start_shift_update",methods=["GET","POST"])
@login_required
@end_shift_first
@check_schema
def start_shift_update():
        "Start Update of Shift Figures"
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                if request.method == "POST":
                        day= request.form.get("date")
                        shift_daytime = request.form.get("shift")
                        pumps = Pump.query.all()
                        pumps_dict= create_dict(pumps)
                        tanks = Tank.query.all()
                        tanks_dict= create_dict(tanks)
                        lubes = LubeProduct.query.all()
                        lubes_dict = create_dict(lubes)
                        fuels = Product.query.all()
                        fuels_dict= create_dict(fuels)

                        if  pumps and  tanks:                      
                                shift_underway = Shift_Underway.query.all()
                                shift_underway[0].state = True
                        
                                shift = Shift(date=day,daytime=shift_daytime,prepared_by=session["user"])
                                db.session.add(shift)
                                db.session.flush()
                               
                                shift_underway[0].current_shift = shift.id
                                current_shift = Shift.query.order_by(Shift.id.desc()).first()
                                shift_id = current_shift.id 
                                prev = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                                shift_daytime = current_shift.daytime
                                date = current_shift.date
                        
                                if lubes:
                                        for product in lubes_dict:
                                                prev_qty = LubeQty.query.filter(and_(LubeQty.shift_id==prev.id,LubeQty.product_id==lubes_dict[product].id)).first() if prev else product.qty
                                                prev_qty = prev_qty.qty if prev else lubes_dict[product].qty
                                                lubes_dict[product] = LubeQty(shift_id=shift_id,date=date,qty=prev_qty,delivery_qty=0,product_id=lubes_dict[product].id)
                                                db.session.add(lubes_dict[product])
                                                db.session.flush()
                                for pump in pumps_dict:
                                        product = db.session.query(Tank,Product,Pump).filter(and_(Tank.product_id == Product.id,Tank.id==Pump.tank_id,Pump.id == pumps_dict[pump].id)).first()
                                        product_id = product[1].id
                                        if prev:
                                                prev_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev.id,PumpReading.pump_id==pumps_dict[pump].id)).first()
                                                litre_reading = prev_reading.litre_reading if prev_reading else pump.litre_reading
                                                money_reading = prev_reading.money_reading if prev_reading else pump.money_reading
                                                pumps_dict[pump] =PumpReading(date=date,product_id=product_id,litre_reading=litre_reading,money_reading=money_reading,pump_id=pumps_dict[pump].id,shift_id=shift_id)
                                        else:
                                                pumps_dict[pump] =PumpReading(date=date,product_id=product_id,litre_reading=pumps_dict[pump].litre_reading,money_reading=pumps_dict[pump].money_reading,pump_id=pumps_dict[pump].id,shift_id=shift_id)
                                        db.session.add(pumps_dict[pump])
                                        db.session.flush()
                                for tank in tanks_dict:      
                                        if prev:
                                                prev_dip = TankDip.query.filter(and_(TankDip.shift_id==prev.id,TankDip.tank_id==tanks_dict[tank].id)).first()
                                                dip = prev_dip.dip if prev_dip else tanks_dict[tank].dip
                                                tanks_dict[tank] = TankDip(date=date,dip=dip,tank_id=tanks_dict[tank].id,shift_id=shift_id)
                                        else:
                                                tanks_dict[tank] = TankDip(date=date,dip=tanks_dict[tank].dip,tank_id=tanks_dict[tank].id,shift_id=shift_id)
                                        db.session.add(tanks_dict[tank])
                                        db.session.flush()
                                for tank in tanks:
                                        product = db.session.query(Tank,Product).filter(and_(Tank.product_id == Product.id,Tank.id == tank.id)).first()
                                        product_id = product[1].id
                                        fuel_delivery = Fuel_Delivery(date=date,shift_id=shift_id,tank_id=tank.id,qty=0,product_id=product_id,document_number='0000')
                                        db.session.add(fuel_delivery)
                                        db.session.flush()
                             
                               
                                for i in fuels_dict:
                                        fuels_dict[i] = Price(date=date,shift_id=shift_id,product_id=fuels_dict[i].id,cost_price=fuels_dict[i].cost_price,selling_price=fuels_dict[i].selling_price)
                                        db.session.add(fuels_dict[i])
                                        db.session.flush()
                                
                                        
                                session["shift"]  = shift_id
                                session["shift_underway"]=shift_underway[0].state
                                shift_underway[0].current_shift = shift_id
                                db.session.commit()
                                flash("Shift Started")
                                return redirect(url_for('ss26'))
                                        
                        
                        #Unfinished set up of products              
                        else:
                                flash("Please finish set up")
                                return redirect(url_for('products'))

                                        
                # Request is GET
                else:
                        return render_template("start_shift_update.html")

@app.route("/end_shift_update",methods=["POST"])
@view_only
@start_shift_first
@check_schema
@login_required
def end_shift_update():
        "End Update of Shift Figures"
        # first check if cash up on lubes has been done
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_underway = Shift_Underway.query.all()
                shift_id = shift_underway[0].current_shift
                lubes = LubeProduct.query.all()
                check_cash_up = LubesCashUp.query.filter_by(shift_id=shift_id).first()
                if lubes:
                        if check_cash_up:
                                shift_underway[0].state = False
                                db.session.commit()
                                flash('Shift Ended')
                                return redirect(url_for('get_driveway'))
                        else:
                                flash('Do cash up on lubes')
                                return redirect(url_for('shift_lube_sales'))
                else:
                        shift_underway[0].state = False
                        db.session.commit()
                        session["shift_underway"]=False
                        flash('Shift Ended')
                        return redirect(url_for('get_driveway'))

        

@app.route("/driveway/edit",methods=["GET","POST"])
@view_only
@check_schema
@login_required
def readings_entry():
        """Edit previous driveways"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
@check_schema
def price_change():
        """ Edit Price Change Outside shift update"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_id = int(request.form.get("shift"))
                cost_price = request.form.get("cost_price")
                selling_price = request.form.get("selling_price")
                product= Product.query.filter_by(id=request.form.get("product")).first()
                cost_price = request.form.get("cost_price")
                price = Price.query.filter(and_(Price.shift_id==shift_id,Price.product_id==product.id)).first()
                price.cost_price = cost_price
                price.selling_price= selling_price
                product.price = selling_price
                db.session.commit()
                return redirect(url_for('readings_entry'))

@app.route("/driveway/edit/pump_readings_entry",methods=["GET","POST"])
@view_only
@admin_required
@check_schema
@login_required
def pump_readings_entry():
        """Edit readings for pumps """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_id = int(request.form.get("shift"))
                pump_id= request.form.get("pump_name")
                pump = Pump.query.get(pump_id)
                litre_reading = request.form.get("litre_reading")
                money_reading = request.form.get("money_reading")
                reading = PumpReading.query.filter(and_(PumpReading.shift_id==shift_id,PumpReading.pump_id==pump_id)).first()
                reading.money_reading = money_reading
                reading.litre_reading = litre_reading
                pump.money_reading = money_reading
                pump.litre_reading = litre_reading
                db.session.commit()
                return redirect(url_for('readings_entry'))


@app.route("/driveway/edit/tank_dips_entry",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def tank_dips_entry():
        """Edit Dips for Tanks """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_id = int(request.form.get("shift"))
                tank_id = request.form.get("tank_name")
                tank = Tank.query.get(tank_id)
                tank_dip = request.form.get("tank_dip")
                shift_dip = TankDip.query.filter(and_(TankDip.tank_id==tank_id,TankDip.shift_id==shift_id)).first()
                shift_dip.dip = tank_dip
                tank.dip = tank_dip
                #db.session.query(TankDip).filter(and_(TankDip.tank_id == tank_id,TankDip.shift_id ==shift_id)).update({TankDip.dip: tank_dip}, synchronize_session = False)
                db.session.commit()
                return redirect(url_for('readings_entry'))


@app.route("/driveway/edit/fuel_delivery",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def fuel_delivery():
        """Edit  Fuel Deliveries"""  
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}): 
                shift_id = int(request.form.get("shift"))
                tank_id= request.form.get("tank_name")
                delivery =request.form.get("litres_delivered")
                fuel_delivery = Fuel_Delivery.query.filter(and_(Fuel_Delivery.tank_id==tank_id,Fuel_Delivery.shift_id==shift_id)).first()
                #db.session.query(Fuel_Delivery).filter(and_(Fuel_Delivery.tank_id == tank_id,Fuel_Delivery.shift_id ==shift_id)).update({Fuel_Delivery.qty: delivery}, synchronize_session = False)
                db.session.commit()
                return redirect(url_for('readings_entry'))

@app.route("/driveway/edit/update_customer_sales",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def update_customer_sales():
        """Sales Invoices"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
@view_only
@admin_required
@check_schema
@login_required
def update_sales_receipts():
        """Invoices for cash sales"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_id = int(request.form.get("shift"))
                current_shift = Shift.query.get(shift_id)
                date = current_shift.date
                customer_id= int(request.form.get("account"))
                customer = Customer.query.get(customer_id)
                account = Account.query.filter_by(account_name=customer.name).first()
                amount= float(request.form.get("amount"))
                invoices = Invoice.query.filter(and_(Invoice.shift_id ==shift_id,Invoice.customer_id==customer_id)).all()
                receipt = SaleReceipt.query.filter(and_(SaleReceipt.shift_id==shift_id,SaleReceipt.account_id==account.id)).first()
                receipt.amount = amount
                #delete previous invoices to start afresh
                for invoice in invoices:
                        db.session.delete(invoice)
                

                cash_invoices = cash_sales(amount,customer_id,shift_id,date)# add invoices to cash customer account
                if cash_invoices:
                        db.session.commit()

                
                return redirect(url_for('readings_entry'))

@app.route("/company_information/company_details",methods=["GET","POST"])
@admin_required
@check_schema
@login_required
def company_details():
        """Managing Company Details"""
        
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                tenant= Tenant.query.get(session['tenant'])
               
                return render_template("company_details.html",tenant=tenant)

@app.route("/company_information/edit_details",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def edit_company_details():
        """Edit Company Details"""
        
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):

                tenant = Tenant.query.get(session["tenant"])
                tenant.name = request.form.get("name").capitalize()
                tenant.address = request.form.get("address").capitalize()
                tenant.email = request.form.get("email")
                tenant.contact_person= request.form.get("contact_person").capitalize()
                tenant.phone_number = request.form.get("phone")
                db.session.commit()
               
                return redirect(url_for('company_details'))


@app.route("/company_information/users",methods=["GET","POST"])
@admin_required
@check_schema
@login_required
def manage_users():
        """Managing Users"""
        if request.method == "GET":
                with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                        users_roles = db.session.query(User,Role).filter(Role.id == User.role_id).all()
                        users= User.query.all()
                        roles = Role.query.all()
                        return render_template("manageusers.html",roles=roles,users_roles=users_roles,users=users)



@app.route("/company_information/users/add_user",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def add_user():
        """Add User"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                username=request.form.get("username").capitalize()
                password=generate_password_hash(request.form.get("password"))
                role_id = request.form.get("role")
                tenant_id = request.form.get("tenant")
                user = User(username=username,password=password,role_id=role_id,tenant_id=tenant_id)
                user_exists = bool(User.query.filter_by(username=username).first())
                if user_exists:
                        flash("User already exists, Try using another username!!")
                        return redirect(url_for('manage_users'))
                else:
                        try:
                                db.session.add(user)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash("There was an error")
                        else:
                        
                                flash('User Successfully Added')
                                return redirect(url_for('manage_users'))

@app.route("/company_information/users/edit_user",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def edit_user():
        """Edit User Information"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                username = request.form.get("username")
                user = User.query.filter_by(username=username).first()
                user.password =request.form.get("password")
                user.role_id=  request.form.get("role")
                db.session.commit()
                flash('User Successfully Updated')
                return redirect(url_for('manage_users'))

@app.route("/company_information/users/delete_user",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def delete_user():
        """Deletes Users"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                user = db.session.query(User).get(int(request.form.get("users")))
                try:
                        db.session.delete(user)  
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("Could not delete user")
                        return redirect(url_for('manage_users'))
                else:

                        flash('User Successfully Removed!!')
                        return redirect(url_for('manage_users'))



@app.route("/inventory/pumps/",methods=["GET","POST"])
@check_schema
@login_required
def pumps():
        """Pump List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                pump_tank = db.session.query(Tank,Pump).filter(Tank.id == Pump.tank_id).all()
                pumps =  Pump.query.all()
                tanks = Tank.query.all()
                return render_template("pumps.html",pumps=pumps,pump_tank=pump_tank,tanks=tanks)
        

@app.route("/inventory/pumps/add_pump",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def add_pump():

        """Add Pump"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_underway = Shift_Underway.query.all()
                ######
                s = Shift.query.order_by(Shift.id.desc()).all()
                name=request.form.get("pump_name").capitalize()
                name = name.strip()
                tank_id=request.form.get("tank")
                litre_reading = request.form.get("litre_reading").strip() # opening readings
                money_reading = request.form.get("money_reading").strip()
                try:
                        tank = Tank.query.get(tank_id)
                except:
                        flash("Add tank to associate pump with")
                        return redirect(url_for('tanks'))
                pump = Pump(name=name,tank_id=tank_id,litre_reading=litre_reading,money_reading=money_reading)
                
                
                try:
                        db.session.add(pump)
                        db.session.flush()
                        product = db.session.query(Tank,Product,Pump).filter(and_(Tank.product_id == Product.id,Tank.id==Pump.tank_id,Tank.id == tank_id,Pump.id == pump.id)).first()
                        product_id = product[1].id
                        for shift in s:
                                open_reading = PumpReading(date=shift.date,product_id=product_id,litre_reading=litre_reading,money_reading=money_reading,pump_id=pump.id,shift_id=shift.id)
                                db.session.add(open_reading)
                                db.session.flush()
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error adding pump to database")
                        return redirect(url_for('pumps'))
                else:
                        flash('Pump Successfully Added !!')
                        return redirect(url_for('pumps'))

                                        
                                        

                       
@app.route("/inventory/pumps/delete_pump",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_pump():
        """Delete Pump"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                pump = db.session.query(Pump).get(int(request.form.get("pumps")))
                try:
                        db.session.delete(pump)   
                        db.session.commit()
                               
                except:
                        db.session.rollback()
                        flash("Can not delete record !!")
                        return redirect(url_for('pumps'))
                else:
                        flash('Pump Successfully Removed!!')
                        return redirect(url_for('pumps'))

@app.route("/inventory/pumps/edit_pump",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_pump():
        """Modify Pump Settings"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                pump_id = request.form.get("pump_id")
                name = request.form.get("name")
                pump = Pump.query.get(pump_id)
                pump.tank_id =request.form.get("tank")
                pump.name=  name
                db.session.commit()
                flash('Pump Successfully Updated')
                return redirect(url_for('pump'))

@app.route("/inventory/tanks/add_tank",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_tank():
        """Add Tank"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_underway = Shift_Underway.query.all()
                name =request.form.get("tank_name").capitalize()
                name = name.strip()
                product_id=request.form.get("product")
                dip = request.form.get("dip")
                date= request.form.get("date")
                s = Shift.query.order_by(Shift.id.desc()).all()

                tank = Tank(name=name,product_id=product_id,dip=dip)
                try:
                        db.session.add(tank)
                        db.session.flush()
                        for shift in s:
                                shift_dip = TankDip(date=shift.date,shift_id=shift.id,dip=dip,tank_id=tank.id)
                                db.session.add(shift_dip)
                                db.session.flush()
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was a problem whilst adding tank")
                        return redirect(url_for('tanks'))
                else:
                        flash("Tank Added Successfully !!")
                        return redirect(url_for('tanks'))
                #check if there is a current shift going on and make the update to the correct previous shift
               


@app.route("/inventory/tanks/delete_tank",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_tank():
        """Delete Tank"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                tank = db.session.query(Tank).get(int(request.form.get("tanks")))
                try:
                        db.session.delete(tank)    
                        db.session.commit()
                        
                except:
                        db.session.rollback()
                        flash("Can not Delete Record")
                        return redirect(url_for('tanks'))
                else:
                        
                        flash('Tank Successfully Removed!!')
                        return redirect(url_for('tanks'))

@app.route("/inventory/tanks/edit_tank",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_tank():
        """Modify Tank Settings"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                tank_id = request.form.get("tank_id")
                tank = Tank.query.get(tank_id)
                name =request.form.get("tank")
                product_id = request.form.get("product")
                tank.name=  name
                tank.product_id = product_id
                db.session.commit()
                flash('Tank Successfully Updated')
                return redirect(url_for('tanks'))


@app.route("/inventory/tanks/",methods=["GET","POST"])
@check_schema
@login_required
def tanks():
        """Tank List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                tank_product = db.session.query(Tank,Product).filter(Product.id == Tank.product_id).all()
                tanks = Tank.query.all()
                products = Product.query.all()
                return render_template("tanks.html",tanks=tanks,products=products,tank_product=tank_product)

@app.route("/inventory/fuel_products/",methods=["GET","POST"])
@admin_required
@check_schema
@login_required
def products():
        """Product List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                products = Product.query.all()
                return render_template("products.html",products=products)

@app.route("/inventory/fuel_products/add_product",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_product():
        """Add Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name=request.form.get("product_name").capitalize()
                price=request.form.get("price")
                cost = request.form.get("cost")
                qty=request.form.get("qty")
                product_type=request.form.get("product_type")
                try:
                        product = Product(name=name,selling_price=price,qty=qty,product_type=product_type,cost_price=cost)
                        db.session.add(product)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error")
                        return redirect(url_for('products'))
                
                else:
                        flash("Product Added !!")
                        return redirect(url_for('products'))


@app.route("/inventory/fuel_products/delete_product",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_product():
        """Delete Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                product = db.session.query(Product).get(int(request.form.get("products")))
                reading_entry = PumpReading.query.filter_by(product_id=int(request.form.get("products"))).all()
                try:
                        db.session.delete(product)   
                        db.session.commit()
                        
                except:
                        db.session.rollback()
                        flash("Can not delete Record")
                        return redirect(url_for('products'))
                else:
                        
                        flash('Product Successfully Removed!!')
                        return redirect(url_for('products'))


@app.route("/inventory/lubes/",methods=["GET","POST"])
@check_schema
@login_required
def lube_products():
        """Lubes Product List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift = Shift.query.order_by(Shift.id.desc()).first()
                products = LubeProduct.query.all()
                return render_template("lube_products.html",products=products,shift=shift)

@app.route("/inventory/lubes/add_lube_product/",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_lube_product():
        """Add Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift = Shift.query.order_by(Shift.id.desc()).first()
                
                #####
                name=request.form.get("product_name")
                cost_price=request.form.get("cost_price")
                selling_price=request.form.get("selling_price")
                mls=request.form.get("mls")
                open_qty = request.form.get("open_qty")

                s = Shift.query.order_by(Shift.id.desc()).all()
        
                product = LubeProduct(name=name,cost_price=cost_price,selling_price=selling_price,mls=mls,qty=open_qty)
                
                try:
                        db.session.add(product)
                        db.session.flush()
                        for shift in s:
                                qty = LubeQty(shift_id = shift.id,date=shift.date,qty=open_qty,delivery_qty=0,product_id=product.id)
                                db.session.add(qty)
                                db.session.flush()
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error adding product to database")
                        return redirect(url_for('lube_products'))
                else:
                        flash("Product Added !!")
                        return redirect(url_for('lube_products'))
                #check if there is a current shift going on and make the update to the correct previous shift
                


@app.route("/inventory/lubes/delete_lube_product/",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_lube_product():
        """Delete Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                product = db.session.query(Product).get(int(request.form.get("products")))
                try:
                        db.session.delete(product)   
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was en error")
                        return redirect(url_for('lube_products'))
                else:
                        flash('Product Successfully Removed!!')
                        return redirect(url_for('lube_products'))


@app.route("/inventory/coupons/",methods=["GET","POST"])
@check_schema
@login_required
def coupons():
        """Coupon List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                coupons = Coupon.query.all()
                return render_template("coupons.html",coupons=coupons)

@app.route("/inventory/coupons/add_coupon",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_coupon():
        """Add Coupons"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                coupon = Coupon(name=request.form.get("coupon_name").capitalize(),coupon_qty=request.form.get("coupon_qty"))
                try:
                        db.session.add(coupon)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("Can not add record")
                        return redirect(url_for('coupons'))
                else:
                        flash("Coupon Added !!")
                        return redirect(url_for('coupons'))


@app.route("/inventory/coupons/delete_coupon",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_coupon():
        """Delete Coupon"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                coupon = Coupon.query.get(request.form.get("coupon_id"))
                try:
                        db.session.delete(coupon)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash('Can not delete record')
                        return redirect(url_for('coupons'))
                else:
                        
                        flash('Coupon Successfully Removed!!')
                        return redirect(url_for('coupons'))

@app.route("/customers",methods=["GET","POST"])
@login_required
@check_schema
def customers():
        """Managing Customers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
@admin_required
@check_schema
@login_required
def customer_payment():
        """Managing Customers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                date = request.form.get("date")
                customer_id = request.form.get("customers")
                amount = request.form.get("amount")
                ref = request.form.get("ref") or ""
                try:
                        payment = CustomerPayments(date=date,customer_id=customer_id,amount=amount,ref=ref)
                        db.session.add(payment)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash('There was error adding payment')
                        return redirect(url_for('customers'))
                else:
                        
                        flash('Payment Successfully Added')
                        return redirect(url_for('customers'))

@app.route("/customers/<int:customer_id>",methods=["GET","POST"])
@check_schema
@login_required
def customer(customer_id):
        """Report for single customer"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
@admin_required
@check_schema
@login_required
def add_customer():
        """Add Customer"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name = request.form.get("name").stip().capitalize()
                customer = Customer(name=name,account_type=request.form.get("type"),phone_number=request.form.get("phone"),contact_person=request.form.get("contact_person").capitalize())
                customer_exists = bool(Customer.query.filter_by(name=name).first())
                if customer_exists:
                        flash("User already exists, Try using another  account name!!")
                        return redirect(url_for('customers'))
                else:
                        account_type = request.form.get("type").strip().capitalize()
                        account_name = request.form.get("name").strip().capitalize()
                        if account_type == "Non-Cash":
                                try:
                                        db.session.add(customer)
                                        account = Account(account_name=account_name,account_category="Receivables")
                                        db.session.add(account)
                                        db.session.commit()
                                except:
                                        db.session.rollback()
                                        flash('There was an error')
                                        return redirect(url_for('customers'))
                                else:
                                        
                                        flash('Customer Successfully Added')
                                        return redirect(url_for('customers'))
                        else:
                                        
                                try:
                                        account = Account(account_name=account_name,account_category=account_type)
                                        db.session.add(account)
                                        db.session.add(customer)
                                        db.session.commit()
                                except:
                                        db.session.rollback()
                                        flash("There was an error")
                                        return redirect(url_for('customers'))
                                else:
                                        flash('Customer Successfully Added')
                                        return redirect(url_for('customers'))


@app.route("/customers/edit_customer",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_customer():
        """Edit Customer Information"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name = request.form.get("name").capitalize()
                db.session.query(Customer).filter(Customer.name == name).update({Customer.phone_number: request.form.get("phone")}, synchronize_session = False)
                db.session.query(Customer).filter(Customer.name == request.form.get("name")).update({Customer.contact_person: request.form.get("contact_person")}, synchronize_session = False)
                db.session.commit()
                flash('Customer Successfully Updated')
                return redirect(url_for('customers'))

@app.route("/customers/delete_customer",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_customer():
        """Deletes Customers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                customer = db.session.query(Customer).get(int(request.form.get("customers")))
                invoices = Invoice.query.filter_by(customer_id=customer.id).all()
                payments = CustomerPayments.query.filter_by(customer_id=customer.id).all()
                try:
                        db.session.delete(customer)   
                        db.session.commit()
                        flash("Can not delete record")
                        return redirect(url_for('customers'))
                except:
                        db.session.rollback()
                        flash("Can not delete record")
                        return redirect(url_for('customers'))
                else:
                        
                        flash('Customer Successfully Removed!!')
                        return redirect(url_for('customers'))

#########

@app.route("/suppliers",methods=["GET","POST"])
@check_schema
@login_required
def suppliers():
        """Managing Suppliers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= db.session.query(Supplier,Account).filter(Supplier.name ==Account.account_name).all()
                suppliers = Supplier.query.all()
                # calculate balances
                balances = {}
                for account in accounts:
                        #deliveries = Fuel_Delivery.query.filter_by(supplier=account[0].id).all()
                        payments = PayOut.query.filter_by(pay_out_account=account[1].id).all()
                        #net = sum([i.amount for i in payments]) - sum([i.cost_price*i.qty for i in delveries])
                        net = sum([i.amount for i in payments]) # use above line on database reset, the pains of development !!
                        balances[account[0].name]=net
                return render_template("suppliers.html",suppliers=suppliers,balances=balances)

@app.route("/suppliers/add_supplier",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_supplier():
        """Add Supplier"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name = request.form.get("name").strip().capitalize()
                phone_number=request.form.get("phone").strip().capitalize()
                contact_person=request.form.get("contact_person").capitalize()
                supplier = Supplier(name=name,phone_number=phone_number,contact_person=contact_person)
                supplier_exists = bool(Supplier.query.filter_by(name=name).first())
                if supplier_exists:
                        flash("Supplier already exists, Try using another  account name !!")
                        return redirect(url_for('suppliers'))
                else:
                        try:
                                db.session.add(supplier)
                                account = Account(account_name=name,account_category="Payables")
                                db.session.add(account)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash('There was an error')
                                return redirect(url_for('suppliers'))
                        else:
                                
                                flash('Supplier Successfully Added')
                                return redirect(url_for('suppliers'))
                       

@app.route("/suppliers/edit_supplier",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_supplier():
        """Edit Supplier Information"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                supplier = Supplier.query.get(request.form.get("id"))
                supplier.name = request.form.get("name").strip().capitalize()
                supplier.phone_number=  request.form.get("phone")
                supplier.contact_person= request.form.get("contact_person")
                db.session.commit()
                flash('Supplier Successfully Updated')
                return redirect(url_for('suppliers'))

@app.route("/suppliers/delete_suppliers",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_supplier():
        """Deletes Supplier"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                supplier = db.session.query(Supplier).get(int(request.form.get("suppliers")))
                
                try:
                        db.session.delete(supplier)   
                        db.session.commit()
                        
                except:
                        db.session.rollback()
                        flash("Can not delete record")
                        return redirect(url_for('suppliers'))
                else:
                        
                        flash('Supplier Successfully Removed!!')
                        return redirect(url_for('suppliers'))




@app.route("/suppliers/expenses/",methods=["GET","POST"])
@check_schema
@login_required
def accounts():
        """Managing Expense Accounts"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= Account.query.filter_by(account_category="Expense").all()
                return render_template("accounts.html",accounts=accounts)

@app.route("/suppliers/expenses/delete_account",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_account():
        """Deletes Account"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                account = db.session.query(Account).get(int(request.form.get("accounts")))
                try:
                        db.session.delete(account)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error")
                        return redirect(url_for('accounts'))
                else:
                        
                        flash('Account Successfully Removed!!')
                        return redirect(url_for('accounts'))

@app.route("/suppliers/expenses/add_accounts",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_account():
        """Add Account"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name=request.form.get("name").strip().capitalize()
                account = Account(account_name=name,account_category=request.form.get("category"))
                account_exists = bool(Account.query.filter_by(account_name=request.form.get("name")).first())
                if account_exists:
                        flash("Account already exists, Try using another username!!")
                        return redirect(url_for('accounts'))
                else:
                        try:
                                db.session.add(account)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash("There was an error")
                                return redirect(url_for('accounts'))
                        else:
                                
                                flash('Account Successfully Added')
                                return redirect(url_for('accounts'))

@app.route("/reports/cash_accounts",methods=["GET","POST"])
@check_schema
@login_required
def cash_accounts():
        """Cash Account Report"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= Account.query.filter_by(account_category="Cash").all()
                balances= {}
                for account in accounts:
                        receipts = SaleReceipt.query.filter_by(account_id=account.id).all()
                        payouts = PayOut.query.filter_by(source_account=account.id).all()
                        balance = sum([i.amount for i in receipts])- sum([i.amount for i in payouts])
                        balances[account]=balance
                return render_template("cash_accounts.html",accounts=accounts,balances=balances)




@app.route("/reports/cash_accounts/<int:account_id>",methods=["GET","POST"])
@check_schema
@login_required
def cash_account(account_id):
        """Cash Account """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
@check_schema
@login_required
def daily_payouts(date,cashaccount_id):
        """Expenses Report"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                payouts = db.session.query(PayOut,Account).filter(PayOut.pay_out_account==Account.id,PayOut.date==date,PayOut.source_account==cashaccount_id).all()
                total = sum([i[0].amount for i in payouts])
                return render_template("daily_payouts.html",payouts=payouts,cashaccount_id=cashaccount_id,total=total,date=date)


@app.route("/reports/profit_statement",methods=["GET","POST"])
@login_required
@admin_required
@check_schema
def profit_statement():
        """ Gross Profit Statement as per shift"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                products = Product.query.all()
                products = [product.name for product in products]
                if request.method =="GET":

                        end_date = date.today()
                        start_date = end_date - timedelta(days=900)
                        report = fuel_product_profit_statement(start_date,end_date)
                        total_profit = fuel_daily_profit_report(start_date,end_date)
                        total_litres = fuel_daily_sales(start_date,end_date)
                        

                        return render_template("profit_statement.html",reports=report,start_date=start_date,end_date=end_date,products=products,total_profit=total_profit,total_litres=total_litres)
                        
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        report = fuel_product_profit_statement(start_date,end_date)
                        total_profit = fuel_daily_profit_report(start_date,end_date)
                        total_litres = fuel_daily_sales(start_date,end_date)

                        return render_template("profit_statement.html",reports=report,start_date=start_date,end_date=end_date,products=products,total_profit=total_profit,total_litres=total_litres)
                
@app.route("/reports/sales_analysis",methods=["GET","POST"])
@check_schema
@login_required
def sales_analysis():
        """ Sales Analyis as per shift"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                if request.method =="GET":

                        end_date = date.today()
                        start_date = end_date - timedelta(days=900)
                        report = daily_sales_analysis(start_date,end_date)

                        return render_template("sales_analysis.html",reports=report,start_date=start_date,end_date=end_date)
                        
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        report = daily_sales_analysis(start_date,end_date)


                        return render_template("sales_analysis.html",reports=report,start_date=start_date,end_date=end_date)
                

@app.route("/reports/sales_breakdown/<date>/",methods=["GET","POST"])
@check_schema
@login_required
def sales_breakdown(date):
        """Expenses Report"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.date==date)).all()
                sales_per_customer = total_customer_sales(customer_sales)
                return render_template("sales_breakdown.html",date=date,sales_per_customer=sales_per_customer)



@app.route("/reports/cashup",methods=["GET","POST"])
@check_schema
@login_required
def cash_up_reports():
        """Managing Cash Accounts"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
@check_schema
@login_required
def lubes_cash_up_reports():
        """Managing Cash Accounts"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
@check_schema
@login_required
def tank_variances(tank_id):
        """Tank Variances Report"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                tank = Tank.query.get(tank_id)
                if request.method =="GET":
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                        end_date = current_shift.date if current_shift else "1994-05-04"
                        start_date = end_date - timedelta(days=30) if current_shift else "1994-05-04"
                        tank_dips = get_tank_variance(start_date,end_date,tank_id)

                        return render_template("tank_variances.html",tank_dips=tank_dips,tank=tank)
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        start_date = check_first_date(start_date)

                        tank_dips = get_tank_variance(start_date,end_date,tank_id)

                        return render_template("tank_variances.html",tank_dips=tank_dips,tank=tank)
                
@app.route("/reports/sales_summary",methods=["GET","POST"])
@check_schema
@login_required
def sales_summary():
        """Sales Summary Report"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                if request.method =="GET":
                       
                        products = Product.query.all()
                        
                        return render_template("sales_summary_filter.html",products=products)
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        
                        product = request.form.get("product")
                        products = Product.query.all()
                        if product =="All":
                                tanks = Tank.query.all()
                        else:
                                tanks = Tank.query.filter_by(product_id=product).all()
                        
                        sales_summary= daily_sales_summary(tanks,start_date,end_date)

                        return render_template("sales_summary.html",report=sales_summary,products=products,start_date=start_date,end_date=end_date)

@app.route("/reports/pump_meter_readings",methods=["GET","POST"])
@check_schema
@login_required
def pump_meter_readings():
        """Pump Meter Readings"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                if request.method =="GET":
                       pumps = Pump.query.all()
                       return render_template("pump_readings_filter.html",pumps=pumps)
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        pump_id = request.form.get("pump")
                        pump = Pump.query.get(pump_id)
                        pump_readings = pump_meter_reading(pump_id,start_date,end_date)

                        return render_template("pump_readings.html",report=pump_readings,start_date=start_date,end_date=end_date,pump=pump)


@app.route("/reports/driveway",methods=["GET","POST"])
@check_schema
@login_required
def get_driveway():

        """Query Shift Driveways for a particular day """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                if request.method == "POST":
                        shift_daytime = request.form.get("shift")
                        date = request.form.get("date")
                        pumps = Pump.query.all()
                        tanks = Tank.query.all()
                        if shift_daytime != "Total":
                                current_shift= Shift.query.filter(and_(Shift.date == date,Shift.daytime == shift_daytime)).first()
                                if not current_shift:
                                        flash("No Such Shift exists")
                                        return redirect(url_for('get_driveway'))
                                shift_id = current_shift.id
                                #####
                                prev = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                                prev_shift_id=prev.id if  prev else shift_id
                                ######
                                pump_readings = get_pump_readings(shift_id,prev_shift_id)
                                tank_dips = get_tank_dips(shift_id,prev_shift_id)
                                product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
                                cash_account = Customer.query.filter_by(name="Cash").first()
                                customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Customer.name != "Cash")).all()
                                sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
                                total_sales_ltr= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
                                total_sales_amt= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1][1].selling_price for product in product_sales_ltr])
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
                                total_lubes_shift_sales = lube_sales(shift_id,prev_shift_id)
                                total_lubes_shift_sales=sum([total_lubes_shift_sales[i][5]*total_lubes_shift_sales[i][2] for i in total_lubes_shift_sales])/1000
                                return render_template("get_driveway.html",avg_sales=avg_sales,mnth_sales=mnth_sales,lubes_daily_sale=lubes_daily_sale,
                                lubes_mnth_sales=lubes_mnth_sales,lube_avg=lube_avg,total_lubes_shift_sales=total_lubes_shift_sales,
                                products=products,accounts=accounts,cash_customers=cash_customers,customers=customers,
                                cash_up=cash_up,total_cash_expenses=total_cash_expenses,expenses=expenses,sales_breakdown=sales_breakdown,
                                shift=current_shift,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,
                                pumps=pumps,tanks=tanks,product_sales_ltr=product_sales_ltr,total_sales_ltr=total_sales_ltr,total_sales_amt=total_sales_amt)
                        else:
                                #Driveway for the day
                                current_shift= Shift.query.filter_by(date=date).order_by(Shift.id.desc()).first()
                                if not current_shift:
                                        flash('No such shift exists')
                                        return redirect(url_for('get_driveway'))
                                shift_id = current_shift.id
                                prev_date = current_shift.date -timedelta(days=1)
                                prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
                                if prev_shift:
                                        prev_shift_id = prev_shift.id
                                else:
                                        prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                                        prev_shift_id = prev_shift.id if prev_shift else shift_id
                                pump_readings = get_pump_readings(shift_id,prev_shift_id)
                                pumps = Pump.query.all()
                                tank_dips = get_tank_dips(shift_id,prev_shift_id)
                                tanks = Tank.query.all()
                                product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
                                cash_account = Customer.query.filter_by(name="Cash").first()
                                customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Customer.name != "Cash")).all()
                                sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
                                total_sales_ltr= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
                                total_sales_amt= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1][1].selling_price for product in product_sales_ltr])
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
                                total_lubes_shift_sales = lube_sales(shift_id,prev_shift_id)
                                total_lubes_shift_sales=sum([total_lubes_shift_sales[i][5]*total_lubes_shift_sales[i][2] for i in total_lubes_shift_sales])/1000
                                return render_template("get_driveway.html",avg_sales=avg_sales,mnth_sales=mnth_sales,lubes_daily_sale=lubes_daily_sale,
                                lubes_mnth_sales=lubes_mnth_sales,lube_avg=lube_avg,total_lubes_shift_sales=total_lubes_shift_sales,
                                products=products,accounts=accounts,cash_customers=cash_customers,customers=customers,
                                cash_up=cash_up,total_cash_expenses=total_cash_expenses,expenses=expenses,sales_breakdown=sales_breakdown,
                                shift=current_shift,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,
                                pumps=pumps,tanks=tanks,total_sales_amt=total_sales_amt,total_sales_ltr=total_sales_ltr,product_sales_ltr=product_sales_ltr)        
                        
                else:

                       
                        shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                        
                        if shifts:
                                current_shift = shifts[0]
                                prev_shift = shifts[1] if len(shifts)>1 else shifts[0]
                                shift_daytime = current_shift.daytime
                                shift_id = current_shift.id
                                date = current_shift.date
                                prev_shift_id = prev_shift.id
                                pump_readings = get_pump_readings(shift_id,prev_shift_id)
                                pumps = Pump.query.all()
                                tank_dips = get_tank_dips(shift_id,prev_shift_id)
                                tanks = Tank.query.all()
                                product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
                                cash_account = Customer.query.filter_by(name="Cash").first()
                                customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Customer.name !="Cash"))
                                sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
                                total_sales_ltr= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
                                total_sales_amt= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1][1].selling_price for product in product_sales_ltr])
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
                                shift=current_shift,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,
                                pumps=pumps,tanks=tanks,product_sales_ltr=product_sales_ltr,total_sales_amt=total_sales_amt,total_sales_ltr=total_sales_ltr)
                        else:
                                flash("No shift updated yet")
                                return redirect(url_for('start_shift_update'))
                                



@app.route("/ss26",methods=["GET"])
@start_shift_first
@check_schema
@login_required
def ss26():

        """UPDATE DRIVEWAY DATA """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):      
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                #######
                shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                if shifts:
                        current_shift = shifts[0]
                        prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        date = current_shift.date
                        prev_shift_id = prev_shift.id
                        pump_readings = get_pump_readings(shift_id,prev_shift_id)
                        pumps = Pump.query.all()
                        tank_dips = get_tank_dips(shift_id,prev_shift_id)
                        tanks = Tank.query.all()
                        product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
                        cash_account = Customer.query.filter_by(name="Cash").first()
                        customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Customer.name != "Cash")).all()
                        sales_breakdown = total_customer_sales(customer_sales) # calculate total sales per customer excl cash (refer to helpers)
                        total_sales_ltr= sum([product_sales_ltr[product][0] for product in product_sales_ltr])
                        total_sales_amt= sum([product_sales_ltr[product][0]*product_sales_ltr[product][1][1].selling_price for product in product_sales_ltr])
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
                        shift=current_shift,date=date,shift_daytime=shift_daytime,tank_dips=tank_dips,pump_readings=pump_readings,
                        pumps=pumps,tanks=tanks,product_sales_ltr=product_sales_ltr,total_sales_amt=total_sales_amt,total_sales_ltr=total_sales_ltr)
                else:
                        flash("NO SHIFT STARTED YET")
                        return redirect ('start_shift_update')


@app.route("/update_pump_litre_readings",methods=['POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def update_pump_litre_readings():


        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                
                shift_id = current_shift.id
               
                pump = Pump.query.filter_by(name=request.form.get("pump")).first()
                pump_id = pump.id
                litre_reading = request.form.get("litre_reading")
                reading = PumpReading.query.filter(and_(PumpReading.pump_id == pump_id,PumpReading.shift_id== shift_id)).first()
                pump.litre_reading = litre_reading
                reading.litre_reading = litre_reading
                #db.session.query(PumpReading).filter(and_(PumpReading.pump_id == pump_id,PumpReading.shift_id== shift_id)).update({PumpReading.litre_reading: reading}, synchronize_session = False)
                db.session.commit()

                return redirect('ss26')

@app.route("/update_pump_money_readings",methods=['POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def update_pump_money_readings():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                pump = Pump.query.filter_by(name=request.form.get("pump")).first()# get pumpid
                pump_id = pump.id
                reading = PumpReading.query.filter(and_(PumpReading.pump_id == pump_id,PumpReading.shift_id== shift_id)).first()
                money_reading = request.form.get("money_reading")
                reading.money_reading = money_reading
                pump.money_reading = money_reading

                db.session.commit()

                return redirect('ss26')


@app.route("/update_tank_dips",methods=['POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def update_tank_dips():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                tank= Tank.query.filter_by(name=request.form.get("tank")).first()
                tank_id = tank.id
                shift_dip = TankDip.query.filter(and_(TankDip.tank_id == tank_id,TankDip.shift_id ==shift_id)).first()
                tank_dip = request.form.get("tank_dip")
                shift_dip.dip = tank_dip
                tank.dip = tank_dip
                db.session.commit()
                return redirect('ss26')

@app.route("/update_fuel_deliveries",methods=['POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def update_fuel_deliveries():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                tank= Tank.query.filter_by(name=request.form.get("tank")).first()
                document = request.form.get("document")
                qty = request.form.get("delivery")
                delivery = Fuel_Delivery(date=current_shift.date,shift_id=shift_id,tank_id=tank.id,qty=qty,product_id=tank.product_id,document_number='0000')
                db.session.add(delivery)
                
                #db.session.query(Fuel_Delivery).filter(and_(Fuel_Delivery.tank_id == tank_id,Fuel_Delivery.shift_id ==shift_id)).update({Fuel_Delivery.qty: qty}, synchronize_session = False)
                db.session.commit()
                return redirect('ss26')

@app.route("/update_cost_prices",methods=['POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def update_cost_prices():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                product= Product.query.filter_by(name=request.form.get("product")).first()
                cost_price = float(request.form.get("cost_price"))
                db.session.query(Price).filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).update({Price.cost_price: cost_price}, synchronize_session = False)
                db.session.commit()
                return redirect('ss26')

@app.route("/update_selling_prices",methods=['POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def update_selling_prices():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_id = current_shift.id
                product= Product.query.filter_by(name=request.form.get("product")).first()
                selling_price = float(request.form.get("selling_price"))
                product.price = selling_price
                db.session.query(Price).filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).update({Price.selling_price: selling_price}, synchronize_session = False)
                db.session.commit()
                return redirect('ss26')

@app.route("/update_shift_date",methods=['POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def update_shift_date():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_id = current_shift.id
                date = request.form.get("date")
                db.session.query(Shift).filter(Shift.id==shift_id).update({Shift.date: date}, synchronize_session = False)
                db.session.commit()
                return redirect('ss26')

@app.route("/update_shift_daytime",methods=['POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def update_shift_daytime():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
@view_only
@start_shift_first
@check_schema
@login_required
def customer_sales():
        """Sales Invoices"""

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
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
@view_only
@start_shift_first
@check_schema
@login_required
def sales_receipts():
        """Invoices for cash sales"""
        
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                date = current_shift.date
                shift_id = current_shift.id
                account= request.form.get("account")
                customer = Customer.query.filter_by(name=account).first()
                cash_account = Account.query.filter_by(account_name=account).first()
                amount= float(request.form.get("amount"))
                receipt = SaleReceipt(date=date,shift_id=shift_id,account_id=cash_account.id,amount=amount)
                db.session.add(receipt)
                cash_invoices = cash_sales(amount,customer.id,shift_id,date)# add invoices to cash customer account
                
                db.session.commit()
                        
                        
                return redirect(url_for('ss26'))


@app.route("/coupon_sales",methods=["POST"])
@view_only
@start_shift_first
@check_schema
@login_required
def coupon_sales():
        """Invoices for coupon sales"""
        
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
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
                
                invoice = Invoice(date=date,product_id=product.id,shift_id=shift_id,customer_id=customer.id,qty=total_litres,price=price.selling_price)
                db.session.add(invoice)
                db.session.commit()
                        
                return redirect(url_for('ss26'))


@app.route("/cash_up",methods=["POST"])
@view_only
@start_shift_first
@check_schema
@login_required
def cash_up():
        """cash up"""

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_id = current_shift.id
                date = current_shift.date
                account = Customer.query.filter_by(name="Cash").first()
                expected_amount = float(request.form.get("expected_amount"))
                cash_sales_amount = float(request.form.get("cash_sales_amount"))
                actual_amount= float(request.form.get("actual_amount"))
                variance= float(request.form.get("variance"))
                cash_account = Account.query.filter_by(account_name="Cash").first()
                amount= cash_sales_amount
                try:
                        cash_up = CashUp(date=date,shift_id=shift_id,sales_amount=cash_sales_amount,expected_amount=expected_amount,actual_amount=actual_amount,variance=variance)
                        receipt = SaleReceipt(date=date,shift_id=shift_id,account_id=cash_account.id,amount=amount)
                        db.session.add(cash_up)
                        db.session.add(receipt)
                        
                        cash_invoices = cash_sales(amount,account.id,shift_id,date)# add invoices to cash customer account
                        
                        db.session.commit()
                        return redirect(url_for('ss26'))
                except Exception as e:
                        db.session.rollback()
                        flash(str(e))
                        return redirect(url_for('ss26'))

@app.route("/payouts",methods=["POST"])
@view_only
@start_shift_first
@check_schema
@login_required
def pay_outs():
        """payouts"""
        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
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
@check_schema
def restart_shift():
        """Restart Shift"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
                shift_underway.state= True
                db.session.commit()
                flash('Shift Restarted !!')
                return redirect(url_for('ss26'))

@app.route("/shift_lube_sales",methods=["POST","GET"])
@view_only
@start_shift_first
@check_schema
@login_required
def shift_lube_sales():
        """LUBE SALES PER SHIFT"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift_underway = Shift_Underway.query.all()
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
@view_only
@check_schema
@login_required
def update_lube_qty():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                req =request.form.get("shift_id")# if the update is from  editing a previous shift
                product = LubeProduct.query.filter_by(name=request.form.get("product")).first() 
                if req:
                        current_shift = Shift.query.get(req)
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        date = current_shift.date
                        product_qty = LubeQty.query.filter(and_(LubeQty.shift_id==current_shift.id,LubeQty.product_id==product.id)).first()
                        if product_qty:
                                try:
                                        product_qty.qty = request.form.get("qty")
                                        db.session.commit()
                                        return redirect(url_for('readings_entry'))
                                except:
                                        db.session.rollback()
                                        flash("There was an error")
                                        return redirect(url_for('readings_entry'))
                                        
                                        
                        else:
                                qty =request.form.get("qty")
                                lube_qty = LubeQty(shift_id=shift_id,date=date,qty=qty,delivery_qty=0,product_id=product.id)
                                try:
                                        db.session.add(lube_qty)
                                        db.session.commit()
                                        return redirect(url_for('readings_entry'))
                                except:
                                        db.session.rollback()
                                        flash("There was an error")
                                        return redirect(url_for('readings_entry'))
                                        
                                        
                else:
                                
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        date = current_shift.date
                        try:
                                lube_qty = LubeQty.query.filter(and_(LubeQty.shift_id==shift_id,LubeQty.product_id==product.id)).first()
                                product.qty = request.form.get("qty")
                                lube_qty.qty = request.form.get("qty")
                                db.session.commit()
                               
                        except:
                                db.session.rollback()
                                flash("There was an error updating qty")
                                return redirect('shift_lube_sales')
                        else:
                                flash('Done')
                                return redirect('shift_lube_sales')
                               

@app.route("/update_lubes_deliveries",methods=['POST'])
@view_only
@check_schema
@login_required
def update_lubes_deliveries():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
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
                                db.session.commit()
                                return redirect('readings_entry')
                        except:
                                db.session.rollback()
                                flash("There was an error")
                                return redirect('readings_entry')
                                
                else:
                                
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        date = current_shift.date
                        try:
                                product = LubeProduct.query.filter_by(name=request.form.get("product")).first() 
                                product = LubeQty.query.filter(and_(LubeQty.shift_id==current_shift.id,LubeQty.product_id==product.id)).first()
                                product.delivery_qty = request.form.get("qty")
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash("There was an error")
                                return redirect('shift_lube_sales')
                        else:
                                
                                return redirect('shift_lube_sales')


@app.route("/update_lubes_cost_prices",methods=['POST'])
@view_only
@check_schema
@login_required
def update_lubes_cost_prices():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                req =request.form.get("shift_id")
                if req:
                        current_shift = Shift.query.get(req)
                else:
                                
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                product = LubeProduct.query.filter_by(name=request.form.get("product")).first() 
                try:
                        product.cost_price = request.form.get("cost_price")
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error")
                else:
                        return redirect('shift_lube_sales')

@app.route("/update_lubes_selling_prices",methods=['POST'])
@view_only
@check_schema
@login_required
def update_lubes_selling_prices():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                req =request.form.get("shift_id")
                if req:
                        current_shift = Shift.query.get(req)
                else:
                                
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                shift_daytime = current_shift.daytime
                shift_id = current_shift.id
                date = current_shift.date
                product = LubeProduct.query.filter_by(name=request.form.get("product")).first() 
                try:
                        product.cost_price = request.form.get("selling_price")
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error")
                else:
                        return redirect('shift_lube_sales')
                

@app.route("/lubes_cash_up",methods=["POST"])
@start_shift_first
@check_schema
@login_required
def lubes_cash_up():
        """lubes cash up"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
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
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error")
                        return redirect(url_for('shift_lube_sales'))

                else:
                        
                        flash("Cash up for Lubricants done!!")
                        return redirect(url_for('ss26'))


@app.route("/forgot_password",methods=['GET','POST'])
def forgot_password():
        """ Reset Password for Admin"""
        if request.method == "GET":
                return render_template("forgot_password.html")
        else:
                email = request.form.get("email")
                code = request.form.get("tenant_code")
                tenant = Tenant.query.filter_by(code=code).first()
                if tenant:
                        password = get_random_string()
                        msg = Message(password,
                        subject="Password Reset-Edriveway",
                                sender="kudakwashechideme@gmail.com",
                                recipients=[email])
                        mail.send(msg)
                        flash("Check you email inbox")
                        return redirect(url_for('index'))


@app.errorhandler(500)
def internal_app_error(error):

        return render_template('error.html'),500

@app.errorhandler(404)
def page_not_found(error):
        
        return render_template('404.html'),404