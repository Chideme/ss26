import os

from flask import Flask, session, render_template,flash,request,redirect,url_for,jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from sqlalchemy import and_, or_,  MetaData,Table
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *
from models import *
from random import randint
from datetime import timedelta,datetime,date
from decimal import Decimal,getcontext


DATABASE_URL=os.getenv("DATABASE_URL")
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}  
app.config["FLASK_ENV"] = os.getenv("FLASK_ENV")
app.secret_key = "KUDAKWASHECHIDEME"
db.init_app(app)
app.config.update(dict(
    DEBUG = False,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = os.getenv("SENDER_MAIL"),
    MAIL_PASSWORD = os.getenv("EMAIL_PASSWORD"),
))
mail = Mail(app)


@app.template_filter()
def currencyFormat(value):
    value = float(value)
    return "${:,.2f}".format(value)

@app.template_filter()
def dateFormat(value):
    
    return value.strftime('%d-%b-%y')

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
                tenant = Tenant(name =company.capitalize(),address=address,company_email=email,database_url=DATABASE_URL,tenant_code=schema,phone_number=phone_number,contact_person=contact_person,schema=schema,active=date.today())
                try:
                        db.session.add(tenant)
                        db.session.flush()
                except:
                        flash("An error occurred",'warning')
                        return render_template("signup.html")
                try:
                        tenant.tenant_code = create_tenant_code(tenant.id)
                        db.session.execute('CREATE SCHEMA IF NOT EXISTS {}'.format(schema))
                        logged_in_users = LoggedInUsers(tenant_id=tenant.id,user_count=0)
                        db.session.add(logged_in_users)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("Account already created use login in page or contact support",'warning')
                        return render_template("signup.html")
                
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
                        today = date.today()
                        password= get_random_string()
                        hash_password = generate_password_hash(password)
                        tenant_id = session['tenant']
                        tenant = Tenant.query.get(tenant_id)
                        create_chart_of_accounts()
                        user=User(username=super_user,password=hash_password,role_id=1,tenant_id=tenant_id,schema=session["schema"])
                        shift_underway = Shift_Underway(state=False,current_shift=0)
                        msg_body = "<h3>Please find your login details :</h3><body><p>Company Code: {}</p><p>User Name: Admin</p><p>Password: {}</p><small>Make sure to change your password once logged in</small></body>".format(tenant.tenant_code,password)
                        db.session.add(shift_underway) 
                        db.session.add(user)
                        db.session.flush()
                        expiration= today + timedelta(days=7)
                        tenant.active = expiration
                        package = Package.query.filter_by(name="free").first()
                        sub = Subscriptions(date=today,package=package.id,tenant_id=tenant_id,amount=0.00,expiration_date=expiration)
                        session["user_id"] = user.id
                        session["user_tenant"]= user.tenant_id
                        session["role_id"] = user.role_id
                        session["shift_underway"]=False
                        try:
                                msg = Message(subject="Welcome Admin!",
                                        sender="kudasystems@gmail.com",
                                        recipients=[tenant.company_email],
                                        html=msg_body)
                                mail.send(msg)
                                db.session.add(sub)
                                db.session.commit()
                                flash('Account Successfully activated. Please use details sent to your email to login.','info')
                                return render_template("login.html")
                                        
                        except:
           
                             
                                flash("Activation Failed",'warning')
                                return render_template("login.html")




@app.route("/login",methods=["GET","POST"])
def login():
        """Log In Company session"""
        session.clear()

       #log in company id

        if request.method == "POST":
                tenant_code = request.form.get("tenant_code")
                company = Tenant.query.filter_by(tenant_code=tenant_code).first()
                try:
                        active =  company.active
                        tenant_id = company.id

                except:
                        flash('Company does not exist, check your code and try again or contact support','warning')
                        return render_template("login.html")

                if company:
                        today = date.today()
                        if active > today:
                                logged_in_users = LoggedInUsers.query.filter_by(tenant_id=tenant_id).first()
                                if logged_in_users.user_count < 4:

                                        session['tenant'] = company.id
                                        session["schema"] = company.schema
                                        logged_in_users.user_count += 1
                                        return redirect(url_for('user_login'))
                                else:
                                        flash('Current number of user reached, ask other users to sign out','warning')
                                        return render_template("login.html")

                        else:
                                sub = Subscriptions.query.filter_by(tenant_id=tenant_id).first()
                                if sub:
                                        session["schema"] = company.schema
                                        session['tenant'] = company.id
                                        flash('Subscription has Expired, contact support +263776393449','warning')
                                        return render_template("login.html")
                                else:
                                        session["schema"] = company.schema
                                        session['tenant'] = company.id
                                        flash('Company is not active. Please activate your company profile','warning')
                                        return redirect(url_for('activate',tenant_schema=session['schema']))
                                        

                else:
                        flash('Company does not exist, check your code and try again or contact support','warning')
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
                        user = User.query.filter_by(username=username).first()
                        org = Tenant.query.get(session["tenant"])
                        shift_underway = Shift_Underway.query.all()
                       
                        if user:
                                if  not check_password_hash(user.password,password) or session['tenant'] != user.tenant_id:
                                        if org.active <= date.today() and User.query.filter_by(session["tenant"]).all() == None:

                                                flash("Please finish setting up your account",'warning')
                                                return redirect(url_for('activate',tenant_schema= org.schema))
                                        else:     
                                                flash("Login details not correct check your details and try again",'warning')
                                                return redirect(url_for('user_login'))
                                else:
                                        session["user_id"] = user.id
                                        session["user"] = user.username
                                        session["user_tenant"]= user.tenant_id
                                        session["role_id"] = user.role_id
                                        session["shift_underway"] = shift_underway[0].state
                                        session["org_name"]= org.name
                                        
                                        flash("Welcome",'info')
                                        return redirect(url_for('finance_dashboard'))
                        else:
                                flash("Login details not correct check your details and try again",'warning')
                                return redirect(url_for('user_login'))
                else:
                        return render_template("login2.html")



@app.route("/logout",methods=["GET"])
@check_schema
def logout():
        """Logs out User"""
        logged_in_users = LoggedInUsers.query.filter_by(tenant_id=session['tenant']).first()
        logged_in_users.user_count  -= 1
        session.clear()
        
        return render_template("login.html")

@app.route("/dashboard/",methods=["GET","POST"])
@login_required
@check_schema
def dashboard():
    """ Dashboard for Forecourt Dashboard"""
    with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
        end_date = date.today()
        start_date =  end_date- timedelta(days=30)
        tanks = Tank.query.all()
        return render_template("dashboard.html",start_date=start_date,end_date=end_date,tanks=tanks)
       


@app.route("/dashboard/reports",methods=["POST"])
@login_required
@check_schema
def dashboard_reports():
        """ Returns JSON Dashboard Reports"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                product = request.form.get("product")
                frequency = request.form.get("frequency")
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                start_date = datetime.strptime(start_date,"%Y-%m-%d")
                end_date = datetime.strptime(end_date,"%Y-%m-%d")
                ###### Tank Variance %
                tank_id = request.form.get("tank")
                if tank_id != "Add Tank":
                        tank_id = int(tank_id)
                        tank_data = tank_variance_daily_report(start_date,end_date,tank_id)
                        t_sorted_date= sorted_dates([i for i in tank_data])
                        tank_info = [tank_data[i] for i in t_sorted_date]
                        tank_dates = [i.strftime('%d-%b-%y')  for i in t_sorted_date]
                else:
                        tank_info = []
                        tank_dates = []
                
                if frequency == "Day-to-day":
                        if product=="Fuel":
                               
                                data = fuel_daily_sales(start_date,end_date)
                                sorted_date= sorted_dates([i for i in data])
                                sales_info = [data[i] for i in sorted_date]
                                sales_dates = [i.strftime('%d-%b-%y')  for i in sorted_date]
                                data = fuel_daily_profit_report(start_date,end_date)
                                p_sorted_date= sorted_dates([i for i in data])
                                profit_info = [data[i] for i in p_sorted_date]
                                profit_dates = [i.strftime('%d-%b-%y')  for i in p_sorted_date]
                                report = jsonify({'SalesDate':sales_dates,'SalesData':sales_info,'ProfitDate':profit_dates,'ProfitData':profit_info,'TankDate':tank_dates,'TankData':tank_info})
                        else:
                                
                                data = lubes_daily_sales(start_date,end_date)
                                sorted_date= sorted_dates([i for i in data])
                                sales_info = [data[i] for i in sorted_date]
                                sales_dates = [i.strftime('%d-%b-%y')  for i in sorted_date]
                                data = lubes_daily_profit_report(start_date,end_date)
                                p_sorted_date= sorted_dates([i for i in data])
                                profit_info = [data[i] for i in p_sorted_date]
                                profit_dates = [i.strftime('%d-%b-%y')  for i in p_sorted_date]
                                report = jsonify({'SalesDate':sales_dates,'SalesData':sales_info,'ProfitDate':profit_dates,'ProfitData':profit_info,'TankDate':tank_dates,'TankData':tank_info})
                if frequency == "Month-to-month":
                        if product =="Fuel":
                               
                                data = fuel_mnth_sales(start_date,end_date)
                                data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
                                sorted_date= sorted_dates([i for i in data])
                                sales_info = [data[i] for i in sorted_date]
                                sales_dates = [i.strftime('%b-%y')  for i in sorted_date]
                                data = fuel_mnth_profit_report(start_date,end_date)
                                data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
                                p_sorted_date= sorted_dates([i for i in data])
                                profit_info = [data[i] for i in p_sorted_date]
                                profit_dates = [i.strftime('%b-%y')  for i in p_sorted_date]
                                report = jsonify({'SalesDate':sales_dates,'SalesData':sales_info,'ProfitDate':profit_dates,'ProfitData':profit_info,'TankDate':tank_dates,'TankData':tank_info})
                        else:
                               
                                data = lubes_mnth_sales(start_date,end_date)
                                data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
                                sorted_date= sorted_dates([i for i in data])
                                sales_info = [data[i] for i in sorted_date]
                                sales_dates = [i.strftime('%b-%y')  for i in sorted_date]
                                data = lubes_mnth_profit_report(start_date,end_date)
                                data = {datetime.strptime(i,"%b-%y").date():data[i] for i in data}
                                p_sorted_date= sorted_dates([i for i in data])
                                profit_info = [data[i] for i in p_sorted_date]
                                profit_dates = [i.strftime('%b-%y')  for i in p_sorted_date]
                                report = jsonify({'SalesDate':sales_dates,'SalesData':sales_info,'ProfitDate':profit_dates,'ProfitData':profit_info,'TankDate':tank_dates,'TankData':tank_info})
                                
                return report

@app.route("/dashboard/finance",methods=["POST","GET"])
@login_required
@check_schema
def finance_dashboard():
        """ Returns JSON Dashboard Reports"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                end_date = date.today()
                start_date =  end_date- timedelta(days=30)
                cash = current_cash_balance()
                ratios = liquidity_ratios(end_date)
                return render_template("finance_dashboard.html",start_date=start_date,end_date=end_date,cash=cash,ratios=ratios)
                

@app.route("/dashboard/finance_reports",methods=["POST"])
@login_required
@check_schema
def dashboard_finance():
        """ Returns JSON Dashboard Reports for finance dashboard"""

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):

                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                frequency = request.form.get("frequency")
                start_date = datetime.strptime(start_date,"%Y-%m-%d")
                end_date = datetime.strptime(end_date,"%Y-%m-%d")
                assets = asset_liabilities(date.today())
                if frequency == "Day-to-day":
                        info = daily_cash_balances(start_date,end_date)
                        dates = [ i for i in info]
                        dates.sort(key = lambda date: datetime.strptime(date, '%d %b %Y'))
                        #sorted_date = sorted_dates(dates)
                        cash_dates =  dates
                        cash_info = [info[i] for i in dates]
                        ######## Revenue
                        sales_data = daily_revenue(start_date,end_date)
                        sales_dates = [i for i in sales_data]
                        sales_dates.sort(key = lambda date: datetime.strptime(date, '%d %b %Y'))
                        sales_info = [sales_data[i] for i in sales_dates]
                         ######## Net Profit Margin
                        margin_data = daily_margin(start_date,end_date)
                        margin_dates = [i for i in margin_data]
                        margin_dates.sort(key = lambda date: datetime.strptime(date, '%d %b %Y'))
                        margin_info = [margin_data[i] for i in margin_dates]
                else:
                        info = monthly_cash_balances(start_date,end_date)
                        dates = [ i for i in info]
                        dates.sort(key = lambda date: datetime.strptime(date, '%b %Y'))
                        #sorted_date = sorted_dates(dates)
                        cash_dates =  dates
                        cash_info = [info[i] for i in dates]
                        ######## Revenue
                        sales_data = monthly_revenue(start_date,end_date)
                        sales_dates = [i for i in sales_data]
                        sales_dates.sort(key = lambda date: datetime.strptime(date, '%b %Y'))
                        sales_info = [sales_data[i] for i in sales_dates]
                        ######## Net Profit Margin
                        margin_data = monthly_margin(start_date,end_date)
                        margin_dates = [i for i in margin_data]
                        margin_dates.sort(key = lambda date: datetime.strptime(date, '%b %Y'))
                        margin_info = [margin_data[i] for i in margin_dates]
                       
                              
                return jsonify({'CashDate':cash_dates,'CashData':cash_info,
                                'Assets':[assets[0]],'Liabilities':[assets[1]],
                                'SalesDates':sales_dates,'SalesData':sales_info,
                                'MarginDates':margin_dates,'MarginData':margin_info})
                


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
                        lubes = Product.query.filter_by(product_type="Lubricants").all()
                        lubes_dict = create_dict(lubes)
                        fuels = Product.query.filter_by(product_type="Fuels").all()
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
                                                prev_qty = LubeQty.query.filter(and_(LubeQty.shift_id==prev.id,LubeQty.product_id==lubes_dict[product].id)).first() if prev else lubes_dict[product].qty
                                                prev_qty = prev_qty.qty if prev else lubes_dict[product].qty
                                                product = LubeQty(shift_id=shift_id,date=date,qty=prev_qty,product_id=lubes_dict[product].id)
                                                db.session.add(product)
                                                db.session.flush()
                                for pump in pumps_dict:
                                        product = db.session.query(Tank,Product,Pump).filter(and_(Tank.product_id == Product.id,Tank.id==Pump.tank_id,Pump.id == pumps_dict[pump].id)).first()
                                        product_id = product[1].id
                                        if prev:
                                                prev_reading = PumpReading.query.filter(and_(PumpReading.shift_id == prev.id,PumpReading.pump_id==pumps_dict[pump].id)).first()
                                                litre_reading = prev_reading.litre_reading if prev_reading else pump.litre_reading
                                                money_reading = prev_reading.money_reading if prev_reading else pump.money_reading
                                                pump=PumpReading(date=date,product_id=product_id,litre_reading=litre_reading,money_reading=money_reading,pump_id=pumps_dict[pump].id,shift_id=shift_id)
                                        else:
                                                pump=PumpReading(date=date,product_id=product_id,litre_reading=pumps_dict[pump].litre_reading,money_reading=pumps_dict[pump].money_reading,pump_id=pumps_dict[pump].id,shift_id=shift_id)
                                        db.session.add(pump)
                                        db.session.flush()
                                for tank in tanks_dict:      
                                        if prev:
                                                prev_dip = TankDip.query.filter(and_(TankDip.shift_id==prev.id,TankDip.tank_id==tanks_dict[tank].id)).first()
                                                dip = prev_dip.dip if prev_dip else tanks_dict[tank].dip
                                                tank= TankDip(date=date,dip=dip,tank_id=tanks_dict[tank].id,shift_id=shift_id)
                                        else:
                                                tank = TankDip(date=date,dip=tanks_dict[tank].dip,tank_id=tanks_dict[tank].id,shift_id=shift_id)
                                        db.session.add(tank)
                                        db.session.flush()
                                """
                                for tank in tanks:
                                        product = db.session.query(Tank,Product).filter(and_(Tank.product_id == Product.id,Tank.id == tank.id)).first()
                                        product_id = product[1].id
                                        supplier = Supplier.query.get(1)
                                        if supplier:
                                                fuel_delivery = Delivery(date=date,shift_id=shift_id,tank_id=tank.id,qty=0,cost_price=product[1].cost_price,supplier=supplier.id,product_id=product_id,document_number='0000')
                                                db.session.add(fuel_delivery)
                                                db.session.flush()
                                        else:
                                                flash("Set Up a supplier to run a shift update")
                                                return redirect(url_for('suppliers'))
                                """
                                # Update prices
                                try:
                                        for i in fuels_dict:
                                                i= Price(date=date,shift_id=shift_id,product_id=fuels_dict[i].id,cost_price=fuels_dict[i].cost_price,selling_price=fuels_dict[i].selling_price,avg_price=fuels_dict[i].avg_price)
                                                db.session.add(i)
                                                db.session.flush()
                                        for i in lubes_dict:
                                                i = Price(date=date,shift_id=shift_id,product_id=lubes_dict[i].id,cost_price=lubes_dict[i].cost_price,selling_price=lubes_dict[i].selling_price,avg_price=lubes_dict[i].avg_price)
                                                db.session.add(i)
                                                db.session.flush()
                                                
                                        session["shift"]  = shift_id
                                        session["shift_underway"]=shift_underway[0].state
                                        shift_underway[0].current_shift = shift_id
                                        db.session.commit()
                                        flash("Shift Started",'info')
                                        return redirect(url_for('driveway_pump_readings'))
                                except:
                                        flash("An error occured",'warning')
                                        return redirect(url_for('driveway_pump_readings'))
                                        
                        
                        #Unfinished set up of products              
                        else:
                                flash("Please finish set up",'warning')
                                return redirect(url_for('products'))

                                        
                # Request is GET
                else:
                        return render_template("start_shift_update.html")

@app.route("/end_shift_update",methods=["GET","POST"])
@view_only
@start_shift_first
@check_schema
@login_required
def end_shift_update():
        "End Update of Shift Figures"
        # first check if cash up on lubes has been done
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                if request.method == "GET":
                        return render_template("end_shift_update.html")
                else:

                        shift_underway = Shift_Underway.query.all()
                        shift_id = shift_underway[0].current_shift
                        lubes = Product.query.filter_by(product_type="Lubricants").all()
                        check_cash_up = CashUp.query.filter_by(shift_id=shift_id).first()
                        check_lube_cash_up = LubesCashUp.query.filter_by(shift_id=shift_id).first()
                        if lubes:
                                if check_lube_cash_up :
                                        if check_cash_up:
                                
                                        
                                                post_all_shift_journals(shift_id)
                                                session["shift_underway"]=False
                                                shift_underway[0].state = False
                                                db.session.commit()
                                                flash('Shift Ended','info')
                                                return redirect(url_for('driveway_report',shift=shift_id))
                                        else :
                                                flash('Do cash up','warning')
                                                return redirect(url_for('driveway_invoices'))
                                else:
                                        flash('Do cash up on lubes','warning')
                                        return redirect(url_for('shift_lube_sales'))
                        else:
                                if check_cash_up:

                                        try:
                                                post_all_shift_journals(shift_id)
                                                shift_underway[0].state = False
                                                db.session.commit()
                                                session["shift_underway"]=False
                                                flash('Shift Ended','info')
                                                return redirect(url_for('driveway_report',shift=shift_id))
                                        except:
                                                flash('Something is wrong','warning')
                                                return redirect(url_for('driveway_pump_readings'))
                                else:
                                        flash('Do cash up ','warning')
                                        return redirect(url_for('driveway_pump_readings')) 

        

@app.route("/driveway/edit",methods=["GET","POST"])
@view_only
@check_schema
@login_required
def readings_entry():
        """Adjust previous driveways"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                pumps = Pump.query.all()
                tanks= Tank.query.all()
                products= Product.query.filter_by(product_type="Fuels").all()
                customers= Customer.query.all()
                suppliers = Supplier.query.all()
                accounts =Account.query.all()
                product_all= Product.query.all()
                lubes = Product.query.filter_by(product_type="Lubricants").all()
                return render_template("readings_entry.html",product_all=product_all,lubes=lubes,tanks=tanks,pumps=pumps,
                                        products=products,customers=customers,suppliers=suppliers,accounts=accounts)

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
                cost_price = request.form.get("cost_price")
                product_id = request.form.get("product")
                product= Product.query.filter_by(id=product_id).first()
                try:
                
                        price = Price.query.filter(and_(Price.shift_id==shift_id,Price.product_id==product.id)).first()
                        price.cost_price = cost_price
                        price.selling_price= selling_price
                        product.selling_price = selling_price
                        product.cost_price = cost_price
                        db.session.commit()
                        flash('Done','info')
                        return redirect(url_for('readings_entry'))
                except:

                        db.session.rollback()
                        flash('Something is wrong, try again','warning')
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
                try:
                        reading = PumpReading.query.filter(and_(PumpReading.shift_id==shift_id,PumpReading.pump_id==pump_id)).first()
                        reading.money_reading = money_reading
                        reading.litre_reading = litre_reading
                        pump.money_reading = money_reading
                        pump.litre_reading = litre_reading
                        db.session.commit()
                        flash('Done','info')
                        return redirect(url_for('readings_entry'))
                except:
                        flash('Something is wrong, try again','warning')
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
                tank_dip = request.form.get("tank_dip")
                tank = Tank.query.get(tank_id)
                
                shift_dip = TankDip.query.filter(and_(TankDip.tank_id==tank_id,TankDip.shift_id==shift_id)).first()
                shift_dip.dip = tank_dip
                tank.dip = tank_dip
                #db.session.query(TankDip).filter(and_(TankDip.tank_id == tank_id,TankDip.shift_id ==shift_id)).update({TankDip.dip: tank_dip}, synchronize_session = False)
                db.session.commit()
                flash('Done','info')
                return redirect(url_for('readings_entry'))






@app.route("/driveway/edit/update_sales_receipts",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def update_sales_receipts():
        """Adjustment for sales invoices outside shift update"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                shift_id = request.form.get("shift")
                shift = Shift.query.get(shift_id)
                date = shift.date
                vehicle_number= request.form.get("vehicle_number")
                driver_name= request.form.get("driver_name")
                customer_id=request.form.get("customers")
                sales_price= float(request.form.get("sales_price"))
                product_id = request.form.get("product")
                qty= float(request.form.get("qty"))
                try:
                        sales_acc = Account.query.filter_by(account_name="Fuel Sales").first()
                        amount = qty * sales_price
                        amount = round(amount,2)
                        post_balance = customer_txn_opening_balance(date,customer_id) + amount
                        txn = CustomerTxn(date=date,txn_type="Invoice",customer_id=customer_id,amount=amount,post_balance=post_balance)
                        db.session.add(txn)
                        db.session.flush()
                        update_customer_balances(date,amount,customer_id,txn.txn_type)
                        customer = Customer.query.get(customer_id)
                        invoice = Invoice(date=date,shift_id=shift_id,product_id=product_id,customer_id=customer_id,qty=qty,price=sales_price,vehicle_number=vehicle_number,driver_name=driver_name,customer_txn_id=txn.id)
                        db.session.add(invoice)
                        db.session.flush()
                        details = "Invoice {}".format(invoice.id)
                        sales_journal=Journal(date=shift.date,details=details,amount=amount,dr=customer.account_id,cr=sales_acc.id,created_by=session['user_id'],updated=False)
                        db.session.add(sales_journal)
                        db.session.commit()
                        
                        return redirect(url_for('readings_entry'))
                except:
                        flash("Something is wrong",'warning')
                        return redirect(url_for('readings_entry'))

@app.route("/driveway/edit/update_deliveries",methods=["POST"])
@view_only
@admin_required
@check_schema
@login_required
def update_deliveries():
        """Adjustment for deliverries outside shift update session"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                shift_id = request.form.get("shift")
                shift = Shift.query.get(shift_id)
                document= request.form.get("document")
                supplier_id=request.form.get("suppliers")
                cost_price= float(request.form.get("cost_price"))
                product_id = request.form.get("product")
                qty= float(request.form.get("qty"))
                product = Product.query.get(product_id)
                price= Price.query.filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).first()
                inventory_acc = Account.query.get(product.account_id)
                amount = qty * cost_price
                amount = round(amount,2)
                new_cost = ((product.cost_price*product.qty) + amount)/(qty +product.qty)
                product.cost_price = cost_price
                product.avg_price = round(new_cost,2)
                price.avg_price = round(new_cost,2)
                price.cost_price = cost_price
                supplier = Supplier.query.get(supplier_id)
                post_balance = supplier_txn_opening_balance(shift.date,supplier.id) + amount
                txn = SupplierTxn(date=shift.date,txn_type="Delivery",supplier_id=supplier.id,amount=amount,post_balance=post_balance)
                db.session.add(txn)
                db.session.flush()
                update_supplier_balances(shift.date,amount,supplier.id,txn.txn_type)
                if product.product_type =="Fuels":
                        tank_id= request.form.get("tank")
                        try:
                                tank = Tank.query.get(tank_id)
                                tank_id = tank.id
                        except:
                                flash('Please select valid tank','warning')
                                return redirect(url_for('readings_entry'))
                        
                        delivery =  Delivery(date=shift.date,shift_id=shift_id,tank_id=tank.id,qty=qty,product_id=product_id,document_number=document,supplier=supplier_id,cost_price=cost_price,supplier_txn_id=txn.id)
                else:
                        delivery =  Delivery(date=shift.date,shift_id=shift_id,qty=qty,product_id=product_id,document_number=document,supplier=supplier_id,cost_price=cost_price,supplier_txn_id=txn.id)
                
                db.session.add(delivery)
                db.session.flush()
                details = "Delivery {}".format(delivery.id)
                delivery_journal=Journal(date=shift.date,details=details,amount=amount,dr=inventory_acc.id,cr=supplier.account_id,created_by=session['user_id'],updated=False)
                db.session.add(delivery_journal)
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
                tenant.name = request.form.get("name")
                tenant.address = request.form.get("address")
                tenant.email = request.form.get("email")
                tenant.contact_person= request.form.get("contact_person")
                tenant.phone_number = request.form.get("phone")
                db.session.commit()
                flash('Done','info')
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
                username=request.form.get("username")
                password=generate_password_hash(request.form.get("password"))
                role_id = request.form.get("role")
                tenant = Tenant.query.filter_by(schema=session['schema']).first()
                user = User(username=username,password=password,role_id=role_id,tenant_id=tenant.id,schema=session['schema'])
                user_exists = bool(User.query.filter_by(username=username).first())
                if user_exists:
                        flash("User already exists, Try using another username",'warning')
                        return redirect(url_for('manage_users'))
                else:
                        try:
                                db.session.add(user)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash("There was an error",'warning')
                                return redirect(url_for('manage_users'))
                        else:
                        
                                flash('User Successfully Added','info')
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
                password  = request.form.get("password")
                password1  = request.form.get("password1")
                if password == password1:
                        try:
                                user = User.query.filter_by(username=username).first()
                                user.password = generate_password_hash(password)
                                user.role_id =  request.form.get("role")
                                db.session.commit()
                                flash('User Successfully Updated','info')
                                return redirect(url_for('manage_users'))
                        except:
                                flash('Something is wrong','warning')
                                return redirect(url_for('manage_users')) 
                else:
                        flash('Passwords Must be the same','warning')
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
                        flash("Could not delete user",'warning')
                        return redirect(url_for('manage_users'))
                else:

                        flash('User Successfully Removed','info')
                        return redirect(url_for('manage_users'))



@app.route("/pumps",methods=["GET","POST"])
@check_schema
@login_required
def pumps():
        """Pump List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                pump_tank = db.session.query(Tank,Pump).filter(Tank.id == Pump.tank_id).all()
                pumps =  Pump.query.order_by(Pump.id.asc()).all()
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
                ######
                s = Shift.query.order_by(Shift.id.desc()).all()
                name=request.form.get("pump_name")
                name = name.strip()
                tank_id=request.form.get("tank")
                litre_reading = request.form.get("litre_reading") # opening readings
                money_reading = request.form.get("money_reading")
                try:
                        tank = Tank.query.get(tank_id)
                except:
                        flash("Add tank to associate pump with",'warning')
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
                        flash("There was an error adding pump",'warning')
                        return redirect(url_for('pumps'))
                else:
                        flash('Pump Successfully Added','info')
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
                        flash("Can not delete record",'danger')
                        return redirect(url_for('pumps'))
                else:
                        flash('Pump Successfully Removed','info')
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
                tank_id = request.form.get("tank")
                if tank_id != "Choose...":
                        pump.tank_id = tank_id
                        pump.name=  name
                        db.session.commit()
                        flash('Pump Successfully Updated','info')
                        return redirect(url_for('pumps'))
                else:
                        flash('Please select tank','warning')
                        return redirect(url_for('pumps'))


@app.route("/inventory/tanks/add_tank",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_tank():
        """Add Tank"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name =request.form.get("tank_name")
                product_id=request.form.get("product")
                dip = request.form.get("dip")
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
                        flash("There was a problem whilst adding tank",'warning')
                        return redirect(url_for('tanks'))
                else:
                        flash("Tank Added Successfully",'info')
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
                        flash("Can not Delete Record",'warning')
                        return redirect(url_for('tanks'))
                else:
                        
                        flash('Tank Successfully Removed','info')
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
                name =request.form.get("name")
                product_id = request.form.get("product")
                tank.name=  name
                tank.product_id = product_id
                db.session.commit()
                flash('Tank Successfully Updated','info')
                return redirect(url_for('tanks'))


@app.route("/tanks",methods=["GET","POST"])
@check_schema
@login_required
def tanks():
        """Tank List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                tank_product = db.session.query(Tank,Product).filter(Product.id == Tank.product_id).all()
                tanks = Tank.query.order_by(Tank.id.asc()).all()
                products = Product.query.filter_by(product_type="Fuels").all()
                return render_template("tanks.html",tanks=tanks,products=products,tank_product=tank_product)

@app.route("/fuel_products",methods=["GET","POST"])
@admin_required
@check_schema
@login_required
def products():
        """Product List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                products = Product.query.filter_by(product_type="Fuels").all()
                accounts = Account.query.filter(Account.code.between(451,460)).all()
                tank_product = db.session.query(Tank,Product).filter(Product.id == Tank.product_id).all()
                prod = Account.query.filter_by(account_name="Fuel Inventory").first()
                qty = {}
                for i in tank_product:
                        if i[1].name not in qty:
                                qty[i[1].name]=i[0].dip
                        else:
                                qty[i[1].name]+=i[0].dip
                return render_template("products.html",products=products,qty=qty,accounts=accounts,prod=prod)

@app.route("/inventory/fuel_products/add_product",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_product():
        """Add Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name=request.form.get("product_name")
                price=request.form.get("price")
                cost = request.form.get("cost")
                product_type=request.form.get("product_type")
                date = request.form.get("date")
                qty = request.form.get("qty")
                account = request.form.get("account")
                unit = 1
                amt = float(qty) * float(cost)
                equity = Account.query.filter_by(account_name="Capital").first()
                
                try:
                        product = Product(name=name,selling_price=price,qty=qty,product_type=product_type,cost_price=cost,avg_price=cost,unit=unit,account_id=account)
                        journal = Journal(date=date,details="Opening Balance",dr=account,cr=equity.id,amount=amt,created_by=session['user_id'],updated=False)
                        db.session.add(product)
                        db.session.add(journal)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error",'warning')
                        return redirect(url_for('products'))
                
                else:
                        flash("Product Added",'info')
                        return redirect(url_for('products'))

@app.route("/inventory/fuel_products/edit_product",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_product():
        """Edit Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name=request.form.get("name")
                product_type=request.form.get("product_type")
                account = int(request.form.get("account"))
                product_id = int(request.form.get("product_id"))
                product = Product.query.get(product_id)
                product.name = name
                product.product_type = product_type
                product.account_id = account
                db.session.commit()
                
                flash("Product Modified",'info')
                return redirect(url_for('products'))

@app.route("/inventory/fuel_products/delete_product",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_product():
        """Delete Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                product = db.session.query(Product).get(int(request.form.get("products")))
                
                try:
                        db.session.delete(product)   
                        db.session.commit()
                        
                except:
                        db.session.rollback()
                        flash("Can not delete Record",'warning')
                        return redirect(url_for('products'))
                else:
                        
                        flash('Product Successfully Removed','info')
                        return redirect(url_for('products'))


@app.route("/inventory/lubes/",methods=["GET","POST"])
@check_schema
@login_required
def lube_products():
        """Lubes Product List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                shift = Shift.query.order_by(Shift.id.desc()).first()
                accounts = Account.query.filter(Account.code.between(451,460)).all()
                products = Product.query.filter_by(product_type="Lubricants").all()
                prod = Account.query.filter_by(account_name="Lubes Inventory").first()
                return render_template("lube_products.html",products=products,shift=shift,accounts=accounts,prod=prod)

@app.route("/inventory/lubes/add_lube_product/",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_lube_product():
        """Add Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
 
                #####
                name=request.form.get("product_name")
                cost_price=float(request.form.get("cost_price"))
                selling_price=float(request.form.get("selling_price"))
                mls =float(request.form.get("unit"))
                open_qty = float(request.form.get("open_qty"))
                date = request.form.get("date")
                product_type = request.form.get("product_type")
                amt = open_qty * cost_price
                equity = Account.query.filter_by(account_name="Capital").first()
                account_id =int(request.form.get("account"))
                s = Shift.query.order_by(Shift.id.desc()).all()
                product = Product(name=name,selling_price=selling_price,qty=open_qty,product_type=product_type,cost_price=cost_price,avg_price=cost_price,unit=mls,account_id=account_id)
                journal = Journal(date=date,details="Opening Balance",dr=account_id,cr=equity.id,amount=amt,created_by=session['user_id'],updated=False)
               
                
                try:
                        db.session.add(product)
                        db.session.add(journal)
                        db.session.flush()  
                        for shift in s:
                                qty = LubeQty(shift_id = shift.id,date=shift.date,qty=open_qty,product_id=product.id)
                                db.session.add(qty)
                                db.session.flush()
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error adding product",'warning')
                        return redirect(url_for('lube_products'))
                else:
                        flash("Product Added",'info')
                        return redirect(url_for('lube_products'))
                #check if there is a current shift going on and make the update to the correct previous shift
                
@app.route("/inventory/lube_products/edit_product",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_lube_product():
        """Edit Lube Product"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name=request.form.get("name")
                product_type=request.form.get("product_type")
                account = int(request.form.get("account"))
                product_id = int(request.form.get("product_id"))
                unit = float(request.form.get("unit"))
                product = Product.query.get(product_id)
                product.name = name
                product.product_type = product_type
                product.account_id = account
                product.unit = float(unit)
                db.session.commit()
                
                flash("Product Modified",'info')
                return redirect(url_for('lube_products'))

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
                        flash("There was en error",'warning')
                        return redirect(url_for('lube_products'))
                else:
                        flash('Product Successfully Removed','info')
                        return redirect(url_for('lube_products'))


@app.route("/inventory/coupons/",methods=["GET","POST"])
@check_schema
@login_required
def coupons():
        """Coupon List"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                coupons = Coupon.query.all()
                accounts = Customer.query.all()
                return render_template("coupons.html",coupons=coupons,accounts=accounts)

@app.route("/inventory/coupons/add_coupon",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_coupon():
        """Add Coupons"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name = request.form.get("coupon_name")
                qty=request.form.get("coupon_qty")
                customer_id = request.form.get("account")
                coupon = Coupon(name=name,coupon_qty=qty,customer_id=customer_id)
                try:
                        db.session.add(coupon)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("Can not add record",'warning')
                        return redirect(url_for('coupons'))
                else:
                        flash("Coupon Added",'info')
                        return redirect(url_for('coupons'))

@app.route("/inventory/coupons/edit_coupon",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_coupon():
        """Edit Coupons"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name = request.form.get("coupon_name")
                coupon_id = request.form.get("coupon_id")
                qty=request.form.get("coupon_qty")
                customer_id = request.form.get("account")
                coupon = Coupon.query.get(coupon_id)
                coupon.customer_id = customer_id
                coupon.coupon_qty = qty
                coupon.name = name
                db.session.commit()
                flash("Done",'info')
                return redirect(url_for('coupons'))

@app.route("/coupons/delete_coupon",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_coupon():
        """Delete Coupon"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                coupon = Coupon.query.get(request.form.get("Coupons"))
                try:
                        db.session.delete(coupon)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash('Can not delete record','warning')
                        return redirect(url_for('coupons'))
                else:
                        
                        flash('Coupon Successfully Removed','info')
                        return redirect(url_for('coupons'))

@app.route("/customers",methods=["GET","POST"])
@login_required
@check_schema
def customers():
        """Managing Customers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                customers= Customer.query.all()
                products = Product.query.all()
                accounts= Account.query.filter(Account.code.between(400,599)).all()
                accounts_dict = {i.id:i for i in accounts}
                cash_accountss = Account.query.filter(Account.code.between(400,450)).all()
                paypoints = Account.query.filter(Account.code.between(400,450)).all()
                cash_ids = [i.id for i in cash_accountss]
                non_cash_customers= Customer.query.filter(Customer.account_id.notin_(cash_ids)).all()
                end_date = date.today()
                # calculate balances
                balances = {}
                for customer in customers:
                        #get last txn
                        #txn = CustomerTxn.query.filter(and_(CustomerTxn.date <= end_date, CustomerTxn.customer_id==customer.id)).order_by(CustomerTxn.id.desc()).first()
                        balances[customer]= customer_txn_opening_balance(end_date,customer.id)
                return render_template("customers.html",products=products,customers=customers,balances=balances,paypoints=paypoints,
                                        cash_accounts=cash_accountss,non_cash_customers=non_cash_customers,accounts=accounts,accounts_dict=accounts_dict)

@app.route("/customers/customer_payment",methods=["POST"])
@admin_required
@check_schema
@login_required
def customer_payment():
        """Managing Customers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                date = request.form.get("date")
                customer_id = request.form.get("customers")
                customer = Customer.query.get(customer_id)
                amount = float(request.form.get("amount"))
                ref = request.form.get("ref") or ""
                paypoint = Account.query.get(request.form.get("paypoint"))
                try:
                        post_balance = customer_txn_opening_balance(date,customer.id) - amount
                        txn = CustomerTxn(date=date,txn_type="Payment",customer_id=customer_id,amount=amount,post_balance=post_balance)
                        db.session.add(txn)
                        db.session.flush()
                        update_customer_balances(date,amount,customer.id,txn.txn_type)
                        payment = CustomerPayments(date=date,customer_id=customer_id,amount=amount,ref=ref,customer_txn_id=txn.id)
                        cr = customer.account_id
                        dr= paypoint.id
                        journal = Journal(date=date,details=ref,amount=amount,dr=dr,cr=cr,created_by=session['user_id'],updated=False)
                        db.session.add(journal)
                        db.session.add(payment)
                        
                        db.session.commit()
                except Exception as e:
                        db.session.rollback()
                        flash(str(e),'warning')
                        return redirect(url_for('customers'))
                else:
                        
                        flash('Payment Successfully Added','info')
                        return redirect(url_for('customers'))

@app.route("/customers/credit_note",methods=["POST"])
@admin_required
@check_schema
@login_required
def credit_note():
        """Create Credit Note"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):

                vehicle_number= request.form.get("vehicle_number")
                sales_price= float(request.form.get("sales_price"))
                product_id = request.form.get("product")
                qty= float(request.form.get("qty"))
                customer_id=request.form.get("customers")
                shift_id = request.form.get("shift")
                shift = Shift.query.get(shift_id)
                customer = Customer.query.get(customer_id)
                account = Account.query.get(customer.account_id)
                sales_return = Account.query.filter_by(account_name="Fuel Sales").first()
                date = shift.date
                amount = qty * sales_price
                amount = round(amount,2)
                post_balance = customer_txn_opening_balance(date,customer_id) - amount
                txn = CustomerTxn(date=date,txn_type="Credit Note",customer_id=customer_id,amount=amount,post_balance=post_balance)
                db.session.add(txn)
                db.session.flush()
                update_customer_balances(date,amount,customer_id,txn.txn_type)
                credit_note = CreditNote(date=date,shift_id=shift_id,product_id=product_id,customer_id=customer_id,qty=qty,price=sales_price,vehicle_number=vehicle_number,driver_name="N/A",customer_txn_id=txn.id)
                db.session.flush()
                details = "Credit note {}".format(credit_note.id)
                ref = "Credit note {} set off".format(credit_note.id)
                if account.account_name != "Accounts Receivables" :
                        post_balance = customer_txn_opening_balance(date,customer_id) - amount
                        txn = CustomerTxn(date=date,txn_type="Payment",customer_id=customer_id,amount=amount,post_balance=post_balance)
                        db.session.add(txn)
                        db.session.flush()
                        update_customer_balances(date,amount,customer_id,txn.txn_type)
                        payment =  CustomerPayments(date=date,customer_id=customer_id,amount=-amount,ref=ref,customer_txn_id=txn.id)
                sales_journal = Journal(date=shift.date,details=details,dr=sales_return.id,cr=customer.account_id,amount=amount,created_by=session['user_id'],updated=False)
                db.session.add(sales_journal)
                db.session.add(payment)
                db.session.add(credit_note)
                db.session.flush()
                db.session.commit()
                flash('Credit note created','info')
                return redirect(url_for('customers'))
                


@app.route("/customers/<int:customer_id>",methods=["GET","POST"])
@check_schema
@login_required
def customer(customer_id):
        """Report for single customer"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                customer = Customer.query.filter_by(id=customer_id).first()
                end_date = date.today()
                net = customer_txn_opening_balance(end_date,customer.id)
        
                if request.method == "POST":
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        report = customer_statement(customer_id,start_date,end_date)

                        return render_template("customer.html",report=report,customer=customer,net=net,start=start_date,end=end_date)
                else:
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        report = customer_statement(customer_id,start_date,end_date)
                        return render_template("customer.html",report=report,customer=customer,net=net,start=start_date,end=end_date)

@app.route("/create_statement/<int:customer_id>",methods=["POST"])
@check_schema
@login_required
def create_statement(customer_id):
        """Report for single customer"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                customer = Customer.query.filter_by(id=customer_id).first()
                tenant = Tenant.query.get(session['tenant'])
                start_date = request.form.get("start_date")
                end_date = request.form.get("end_date")
                report =  customer_statement(customer_id,start_date,end_date)
                dates = sorted_dates([report[i]["date"] for i in report])
                c_txns = CustomerTxn.query.filter(CustomerTxn.customer_id==customer.id,CustomerTxn.date.between(start_date,end_date)).order_by(CustomerTxn.date.asc()).order_by(CustomerTxn.id.asc()).all()
                txns=[i.id for i in c_txns]
                   
                start_date = datetime.strptime(start_date,"%Y-%m-%d")
                end_date = datetime.strptime(end_date,"%Y-%m-%d")
                return render_template("customer_statement.html",txns=txns,tenant=tenant,report=report,customer=customer,start_date=start_date,end_date=end_date)
                

@app.route("/invoice/<int:invoice_id>",methods=["GET","POST"])
@check_schema
@login_required
def invoice(invoice_id):
        """Invoice Details"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                invoice = Invoice.query.get(invoice_id)
                customer = Customer.query.get(invoice.customer_id)
                tenant = Tenant.query.get(session['tenant'])
                product = Product.query.get(invoice.product_id)
                return render_template("invoice.html",customer=customer,invoice=invoice,tenant=tenant,product=product)


@app.route("/customers/add_customer",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_customer():
        """Add Customer"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name = request.form.get("name")
                date = request.form.get("date")
                contact_person=request.form.get("contact_person")
                phone_number=request.form.get("phone")
                opening_balance = float(request.form.get("balance"))
                account = request.form.get("acct")
                acc_type = request.form.get("type")
                details = "Opening Balance - {}".format(name)
                if acc_type =="Non-Cash":
                        debtor = Account.query.filter_by(account_name="Accounts Receivables").first()
                        account_id =debtor.id
                else:
                        debtor = Account.query.get(int(account))
                        account_id =debtor.id
                equity = Account.query.filter_by(account_name="Capital").first()
                if opening_balance !=0:
                        journal = Journal(date=date,details=details,dr=account_id,cr=equity.id,amount=opening_balance,created_by=session['user_id'],updated=False)
                        db.session.add(journal)
                customer = Customer(name=name,account_id=debtor.id,phone_number=phone_number,contact_person=contact_person,opening_balance=opening_balance)
                customer_exists = bool(Customer.query.filter_by(name=name).first())
                
                if customer_exists:
                        flash("User already exists, Try using another  user name",'warning')
                        return redirect(url_for('customers'))
                else:
                
                        try:
                                db.session.add(customer)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash('There was an error','warning')
                                return redirect(url_for('customers'))
                        else:
                                
                                flash('Customer Successfully Added','info')
                                return redirect(url_for('customers'))
                        


@app.route("/customers/edit_customer",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_customer():
        """Edit Customer Information"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                customer_id = request.form.get("customer_id")
                name = request.form.get("name")
                contact_person=request.form.get("contact_person")
                phone_number=request.form.get("phone")
                opening_balance = float(request.form.get("balance"))
                account_id = request.form.get("acct")
                customer = Customer.query.get(int(customer_id))
                customer.name = name
                customer.opening_balance = opening_balance
                customer.phone_number = phone_number
                customer.contact_person = contact_person
                customer.account_d = account_id
                db.session.commit()
                flash('Customer Successfully Updated','info')
                return redirect(url_for('customers'))

@app.route("/customers/delete_customer",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_customer():
        """Deletes Customers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                customer = db.session.query(Customer).get(int(request.form.get("customers")))

                try:
                        db.session.delete(customer)   
                        db.session.commit()
                        flash("Can not delete record",'warning')
                        return redirect(url_for('customers'))
                except:
                        db.session.rollback()
                        flash("Can not delete record",'warning')
                        return redirect(url_for('customers'))
                else:
                        
                        flash('Customer Successfully Removed!!','info')
                        return redirect(url_for('customers'))

#########

@app.route("/suppliers",methods=["GET","POST"])
@check_schema
@login_required
def suppliers():
        """Managing Suppliers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                suppliers = Supplier.query.all()
                products = Product.query.all()
                tanks = Tank.query.all()
                paypoints = Account.query.filter(Account.code.between(500,599)).all()
                # calculate balances
                end_date = date.today()
                balances = {}
                for supplier in suppliers:
                        balances[supplier.name]= supplier_txn_opening_balance(end_date,supplier.id)
                return render_template("suppliers.html",products=products,tanks=tanks,suppliers=suppliers,balances=balances,paypoints=paypoints)


@app.route("/suppliers/supplier_payment",methods=["POST"])
@admin_required
@check_schema
@login_required
def supplier_payment():
        """Managing Suppliers"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                date = request.form.get("date")
                supplier_id = request.form.get("suppliers")
                supplier = Supplier.query.get(supplier_id)
                amount = request.form.get("amount")
                ref = request.form.get("ref") 
                paypoint = Account.query.get(request.form.get("paypoint"))
                try:
                        post_balance = supplier_txn_opening_balance(date,supplier.id) - amount
                        txn = SupplierTxn(date=date,txn_type="Payment",supplier_id=supplier.id,amount=amount,post_balance=post_balance)
                        db.session.add(txn)
                        db.session.flush()
                        update_supplier_balances(date,amount,supplier.id,txn.txn_type)
                        payment = SupplierPayments(date=date,supplier_id=supplier_id,amount=amount,ref=ref,supplier_txn_id=txn.id)
                        dr = supplier.account_id
                        cr= paypoint.id
                        journal = Journal(date=date,details=ref,amount=amount,dr=dr,cr=cr,created_by=session['user_id'],updated=False)
                        db.session.add(journal)
                        db.session.add(payment)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash('There was error adding payment','warning')
                        return redirect(url_for('suppliers'))
                else:
                        
                        flash('Payment Successfully Added','info')
                        return redirect(url_for('suppliers'))


@app.route("/suppliers/debit_note",methods=["POST"])
@admin_required
@check_schema
@login_required
def debit_note():
        """Debit Notes"""  
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}): 
                shift_id = int(request.form.get("shift"))
                shift = Shift.query.get(shift_id)
                qty =float(request.form.get("delivery"))
                document = request.form.get("document")
                supplier_id = request.form.get("supplier")
                cost_price = float(request.form.get("cost_price"))
                product = Product.query.get(int(request.form.get("product")))
                supplier = Supplier.query.get(supplier_id)
                amount = cost_price * qty
                amount = round(amount,2)
                post_balance = supplier_txn_opening_balance(shift.date,supplier.id) - amount
                txn = SupplierTxn(date=shift.date,txn_type="Debit Note",supplier_id=supplier.id,amount=amount,post_balance=post_balance)
                db.session.add(txn)
                db.session.flush()
                update_supplier_balances(shift.date,amount,supplier.id,txn.txn_type)
                if product.product_type =="Fuels":
                        tank_id= request.form.get("tank")
                        try:
                                tank = Tank.query.get(tank_id)
                                tank_id = tank.id
                        except:
                                flash('Please select valid tank','warning')
                                return redirect(url_for('suppliers'))             
                        debitnote = DebitNote(date=shift.date,shift_id=shift_id,tank_id=tank_id,qty=qty,product_id=tank.product_id,document_number=document,supplier=supplier.id,cost_price=cost_price,supplier_txn_id=txn.id)
                        
                else:
                       debitnote = DebitNote(date=shift.date,shift_id=shift_id,qty=qty,product_id=product.id,document_number=document,supplier=supplier.id,cost_price=cost_price,supplier_txn_id=txn.id) 
                db.session.add(debitnote)
                db.session.flush()
                details = "Debit note {}".format(debitnote.id)
                journal =  Journal(date=shift.date,details=details,amount=amount,dr=supplier.account_id,cr=product.account_id,created_by=session['user_id'],updated=False)
                db.session.add(journal)
                db.session.commit()
                flash('Debit note created','info')
                return redirect(url_for('suppliers'))

@app.route("/suppliers/add_supplier",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_supplier():
        """Add Supplier"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name = request.form.get("name")
                date = request.form.get("date")
                phone_number=request.form.get("phone")
                contact_person=request.form.get("contact_person")
                opening_balance = float(request.form.get("balance"))
                details = "Opening Balance - {}".format(name)
                creditor = Account.query.filter_by(account_name="Accounts Payables").first()
                equity = Account.query.filter_by(account_name="Capital").first()
                if opening_balance != 0:
                        journal = Journal(date=date,details=details,dr=equity.id,cr=creditor.id,amount=opening_balance,created_by=session['user_id'],updated=False)
                        db.session.add(journal)
                supplier = Supplier(name=name,phone_number=phone_number,contact_person=contact_person,account_id=creditor.id,opening_balance=opening_balance)
                supplier_exists = bool(Supplier.query.filter_by(name=name).first())
                if supplier_exists:
                        flash("Supplier already exists, Try using another  account name",'warning')
                        return redirect(url_for('suppliers'))
                else:
                        try:
                                db.session.add(supplier)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash('There was an error','warning')
                                return redirect(url_for('suppliers'))
                        else:
                                
                                flash('Supplier Successfully Added','info')
                                return redirect(url_for('suppliers'))
                       

@app.route("/suppliers/edit_supplier",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_supplier():
        """Edit Supplier Information"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                supplier = Supplier.query.get(request.form.get("id"))
                supplier.name = request.form.get("name")
                supplier.phone_number=  request.form.get("phone")
                supplier.contact_person= request.form.get("contact_person")
                db.session.commit()
                flash('Supplier Successfully Updated','info')
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
                        flash("Can not delete record",'warning')
                        return redirect(url_for('suppliers'))
                else:
                        
                        flash('Supplier Successfully Removed','info')
                        return redirect(url_for('suppliers'))

@app.route("/suppliers/<int:supplier_id>",methods=["GET","POST"])
@check_schema
@login_required
def supplier(supplier_id):
        """Report for single supplier"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                supplier = Supplier.query.filter_by(id=supplier_id).first()
                end_date = date.today()
                net= supplier_txn_opening_balance(end_date,customer.id)
                if request.method == "POST":
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        report = supplier_statement(supplier_id,start_date,end_date)
                        
                        return render_template("supplier.html",report=report,supplier=supplier,net=net,start=start_date,end=end_date)
                else:
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        report = supplier_statement(supplier_id,start_date,end_date)
                        return render_template("supplier.html",report=report,supplier=supplier,net=net,start=start_date,end=end_date)

@app.route("/delivery/<int:delivery_id>",methods=["GET","POST"])
@check_schema
@login_required
def delivery(delivery_id):
        """Delivery Details"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                delivery = Delivery.query.get(delivery_id)
                supplier = Supplier.query.get(delivery.supplier)
                tenant = Tenant.query.get(session['tenant'])
                product = Product.query.get(delivery.product_id)
                try:
                        tank = Tank.query.get(delivery.tank_id)
                        tank_name = tank.name
                except:
                        tank_name = "Lubricants"
                
                return render_template("delivery.html",tank_name=tank_name,supplier=supplier,delivery=delivery,tenant=tenant,product=product)


@app.route("/accounts",methods=["GET","POST"])
@check_schema
@login_required
def accounts():
        """Managing  Accounts"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= Account.query.all()
                return render_template("accounts.html",accounts=accounts)

@app.route("/accounts/delete_account",methods=["POST"])
@admin_required
@check_schema
@login_required
def delete_account():
        """Deletes Account"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                account = db.session.query(Account).get(int(request.form.get("accounts")))
                accounts = [501,402,452,453,300,700,900,201,202,100,101,400] # model Chart of accounts, can not delete these.
                if account.code in accounts:
                        flash("You can not delete this account",'warning')
                        return redirect(url_for('accounts'))

                try:
                        db.session.delete(account)
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error",'warning')
                        return redirect(url_for('accounts'))
                else:
                        
                        flash('Account Successfully Removed','info')
                        return redirect(url_for('accounts'))

@app.route("/accounts/add_accounts",methods=["POST"])
@admin_required
@check_schema
@login_required
def add_account():
        """Add Account"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                name=request.form.get("name")
                account_category=request.form.get("category")
                code = account_code(account_category)
                if code == False:
                        flash("You have reached the number of {} accounts".format(account_category))
                        return redirect(url_for('accounts'))
                entry = {"Income":"CR","Expense":"DR","Other Current Asset":"DR","Current Liability":"CR","COGS":"DR",
                "Non Current Asset":"DR","Equity":"CR","Non Current Liability":"CR","Bank":"DR"}
                account = Account(code=code,account_name=name,account_category=account_category,entry=entry[account_category])
                account_exists = bool(Account.query.filter_by(account_name=request.form.get("name")).first())
                if account_exists:
                        flash("Account already exists, Try using another username",'warning')
                        return redirect(url_for('accounts'))
                else:
                        try:
                                db.session.add(account)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash("There was an error",'warning')
                                return redirect(url_for('accounts'))
                        else:
                                
                                flash('Account Successfully Added','info')
                                return redirect(url_for('accounts'))

@app.route("/accounts/edit_accounts",methods=["POST"])
@admin_required
@check_schema
@login_required
def edit_account():
        """Edit Account"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                account_id = request.form.get("account_id")
                name=request.form.get("name")
                account_category=request.form.get("category")
                account = Account.query.get(account_id)
                accounts = [501,402,452,453,300,700,900,201,202,100,101,400] # model Chart of accounts, can not delete these.
                if account.code in accounts:
                        flash("You can not edit this account",'warning')
                        return redirect(url_for('accounts'))
                code = account_code(account_category)
                if code == False:
                        flash("You have reached the number of {} accounts".format(account_category))
                        return redirect(url_for('accounts'))
                entry = {"Income":"CR","Expense":"DR","Other Current Asset":"DR","Current Liability":"CR","COGS":"DR",
                "Non Current Asset":"DR","Equity":"CR","Non Current Liability":"CR","Bank":"DR"}

                account.name = name
                account.entry = entry[account_category]
                account.code= code
                account.account_category= account_category
                db.session.commit()   
                flash('Account Successfully Modified','info')
                return redirect(url_for('accounts'))


@app.route("/create_journal",methods=["POST"])
@check_schema
@login_required
def create_journal():
        """Initiate Journal Entry"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                date = request.form.get("date")
                details = request.form.get("ref")
                amount = request.form.get("amount")
                dr = request.form.get("debit")
                cr = request.form.get("credit")
                journal = Journal_Pending(date=date,details=details,amount=amount,dr=dr,cr=cr,created_by=session['user_id'])
                db.session.add(journal)
                db.session.commit()
                flash('Journal created','info')
                return redirect(url_for('journal_pending'))


@app.route("/post_journal",methods=["POST"])
@check_schema
@admin_required
@login_required
def post_journal():
        """Post Journal Entry"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                i = request.form.get("id")
                j = Journal_Pending.query.get(i)
                journal = Journal(date=j.date,details=j.details,amount=j.amount,dr=j.dr,cr=j.cr,created_by=j.created_by,updated=False)
                db.session.add(journal)
                db.session.delete(j)
                db.session.commit()
                flash('Journal posted, waiting for processing','info')
                return redirect(url_for('journal_pending'))

@app.route("/delete_journal",methods=["POST"])
@check_schema
@login_required
def delete_journal():
        """Delete Journal Entry"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                i = request.form.get("id")
                j = Journal_Pending.query.get(i)
                db.session.delete(j)
                db.session.commit()
                flash('Deleted','info')
                return redirect(url_for('journal_pending'))

@app.route("/journal_pending",methods=["GET","POST"])
@check_schema
@login_required
def journal_pending():
        """Managing  Accounts"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                journals= Journal_Pending.query.all()
                accounts = Account.query.all()
                names = {i.id:i.account_name for i in accounts}
                
                return render_template("journal_pending.html",journals=journals,accounts=accounts,names=names)

@app.route("/process_journals",methods=["GET","POST"])
@check_schema
@login_required
def process_journals():
    """ Post Journals to Legder """
    with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                journals = Journal.query.filter_by(updated=False).order_by(Journal.id.asc()).all()
                accounts = Account.query.all()
                names = {i.id:i.account_name for i in accounts}
                if request.method =="POST":
                        
                        for journal in journals:
                                post_balance = dr_txn_post_balance(journal.date,journal.amount,journal.dr)
                                txn1 = Ledger(date=journal.date,account_id=journal.dr,journal_id=journal.id,txn_type="DR",amount=journal.amount,post_balance =post_balance)
                                post_balance = cr_txn_post_balance(journal.date,journal.amount,journal.cr)
                                txn2 = Ledger(date=journal.date,account_id=journal.cr,journal_id=journal.id,txn_type="CR",amount=journal.amount,post_balance =post_balance)
                                db.session.add(txn1)
                                db.session.add(txn2)
                                update_balances(journal.date,journal.amount,journal.dr,"DR")
                                update_balances(journal.date,journal.amount,journal.cr,"CR")
                                journal.updated = True
                                db.session.flush()
                        db.session.commit()
                        flash('Journals Posted to Ledger','info')
                        return redirect(url_for('process_journals'))
                else:
                        return render_template("process_journals.html",journals=journals,names=names)
                


@app.route("/ledger",methods=["GET","POST"])
@check_schema
@login_required
def ledger():
        """View Transactions"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= Account.query.all()
                if request.method =="GET":
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        account = Account.query.get(1)
                        accounts = Account.query.all()
                        names = {i.id:i.account_name for i in accounts}
                        balance = opening_balance(start_date,account.id)
                        return render_template("ledger.html",accounts=accounts,ac=account,names=names,opening_balance=balance)
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        account_id = int(request.form.get("account"))
                        account = Account.query.get(account_id)
                        accounts = Account.query.all()
                        names = {i.id:i.account_name for i in accounts}
                        balance = opening_balance(start_date,account_id)
                        journals = Journal.query.filter(Journal.date.between(start_date,end_date)).filter(or_(Journal.dr==account_id,Journal.cr==account_id)).order_by(Journal.id.asc()).all()
          
                        return render_template("ledger.html",journals=journals,account_id=account_id,opening_balance=balance,accounts=accounts,start_date=start_date,end_date=end_date,entry=account.entry,ac=account,names=names)

@app.route("/ledger_report",methods=["GET","POST"])
@check_schema
@login_required
def ledger_report():
        """View Transactions"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= Account.query.all()

                if request.method =="GET":
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        account = Account.query.get(1)
                        accounts = Account.query.all()
                        names = {i.id:i.account_name for i in accounts}
                        return render_template("ledger_report.html",accounts=accounts,account=account,names=names)
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        account_id = int(request.form.get("account"))
                        account = Account.query.get(account_id)
                        accounts = Account.query.all()
                        names = {i.id:i.account_name for i in accounts}
                        
                        journals = Ledger.query.filter(and_(Ledger.date.between(start_date,end_date),Ledger.account_id==account_id)).order_by(Ledger.date.asc()).order_by(Ledger.journal_id.asc()).all()

                        return render_template("ledger_report.html",journals=journals,account_id=account_id,accounts=accounts,start_date=start_date,end_date=end_date,account=account,names=names)

@app.route("/trial_balance",methods=["GET","POST"])
@check_schema
@login_required
def trial_balance():
        """View Transactions"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= Account.query.all()
                if request.method =="GET":
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        report = trial_balance_journals(start_date,end_date)
                        r_e = retained_earnings(start_date)
                        return render_template("trial_balance.html",accounts=accounts,report=report,r_e=r_e,start_date=start_date,end_date=end_date)
                        
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        report = trial_balance_journals(start_date,end_date)
                        r_e = retained_earnings(start_date)
                        start_date = datetime.strptime(start_date,"%Y-%m-%d")
                        end_date = datetime.strptime(end_date,"%Y-%m-%d")
                        return render_template("trial_balance.html",accounts=accounts,report=report,r_e=r_e,start_date=start_date,end_date=end_date)

@app.route("/trial_balance_report",methods=["GET","POST"])
@check_schema
@login_required
def trial_balance_report():
        """View Transactions"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= Account.query.all()
                if request.method =="GET":
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        report = trial_balance_ledger(start_date,end_date)
                        r_e = retained_earnings(start_date)
                        return render_template("trial_balance_report.html",accounts=accounts,report=report,r_e=r_e,start_date=start_date,end_date=end_date)
                        
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        report = trial_balance_ledger(start_date,end_date)
                        r_e = retained_earnings(start_date)
                        start_date = datetime.strptime(start_date,"%Y-%m-%d")
                        end_date = datetime.strptime(end_date,"%Y-%m-%d")
                        return render_template("trial_balance_report.html",accounts=accounts,report=report,r_e=r_e,start_date=start_date,end_date=end_date)

@app.route("/pnl",methods=["GET","POST"])
@check_schema
@login_required
def profit_and_loss():
        """Income Statement"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                incomes = Account.query.filter(Account.code.between(100,199)).order_by(Account.code.asc()).all()
                expenses = Account.query.filter(Account.code.between(200,399)).order_by(Account.code.asc()).all()
                if request.method =="GET":
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        report = p_n_l_balances(start_date,end_date)
                        total_revenue = sum(report[i.id] for i in incomes)
                        total_costs = sum(report[i.id] for i in expenses)
                        profit = total_revenue - total_costs
                        
                        return render_template("pnl.html",total_costs=total_costs,total_revenue=total_revenue,profit=profit,incomes=incomes,expenses=expenses,report=report,start_date=start_date,end_date=end_date)
                        
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        report = p_n_l_balances(start_date,end_date)
                        total_revenue = sum(report[i.id] for i in incomes)
                        total_costs = sum(report[i.id] for i in expenses)
                        profit = total_revenue - total_costs
                        start_date = datetime.strptime(start_date,"%Y-%m-%d")
                        end_date = datetime.strptime(end_date,"%Y-%m-%d")
                        return render_template("pnl.html",total_costs=total_costs,total_revenue=total_revenue,profit=profit,incomes=incomes,expenses=expenses,report=report,start_date=start_date,end_date=end_date)


@app.route("/cash_accounts",methods=["GET","POST"])
@check_schema
@login_required
def cash_accounts():
        """Cash Account Report"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                accounts= Account.query.filter(Account.code.between(400,450)).all()
                end_date = date.today()
                balances= {}
                for account in accounts:
                        #get last txn
                        txn = Ledger.query.filter(and_(Ledger.date <= end_date,Ledger.account_id==account.id)).order_by(Ledger.id.desc()).first()
                        balances[account]= round(txn.post_balance,2) if txn else 0
                return render_template("cash_accounts.html",accounts=accounts,balances=balances)




@app.route("/cash_accounts/<int:account_id>",methods=["GET","POST"])
@check_schema
@login_required
def cash_account(account_id):
        """Cash Account"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                account = Account.query.get(account_id)
                end_date = date.today() 
                txn = Ledger.query.filter(and_(Ledger.date <= end_date,Ledger.account_id==account.id)).order_by(Ledger.id.desc()).first()
                balance = round(txn.post_balance,2) if txn else 0

                if request.method == "GET":
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        account_id = account_id

                        report = Ledger.query.filter(Ledger.date.between(start_date,end_date)).filter(or_(Ledger.account_id==account_id)).order_by(Ledger.id.asc()).all()
                        return render_template("cash_account.html",account=account,journals=report,account_id=account_id,balance=balance,start_date=start_date,end_date=end_date)
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        account_id = account_id
                        report = Ledger.query.filter(Ledger.date.between(start_date,end_date)).filter(or_(Ledger.account_id==account_id)).order_by(Ledger.id.asc()).all()
                        
                
                        return render_template("cash_account.html",account=account,journals=report,account_id=account_id,balance=balance,start_date=start_date,end_date=end_date)




@app.route("/profit_statement",methods=["GET","POST"])
@login_required
@admin_required
@check_schema
def profit_statement():
        """ Gross Profit Statement as per shift"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                products = Product.query.filter_by(product_type="Fuels").all()
                products = [product.name for product in products]
                if request.method =="GET":

                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
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
                        start_date = datetime.strptime(start_date,"%Y-%m-%d")
                        end_date = datetime.strptime(end_date,"%Y-%m-%d")
                        return render_template("profit_statement.html",reports=report,start_date=start_date,end_date=end_date,products=products,total_profit=total_profit,total_litres=total_litres)
                
@app.route("/drivewaysummaries",methods=["GET","POST"])
@check_schema
@login_required
def sales_analysis():
        """ Sales Analyis as per shift"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                if request.method =="GET":

                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        report = daily_sales_analysis(start_date,end_date)
                        sales_breakdown = day_sales_breakdown([i for i in report])
                        return render_template("sales_analysis.html",sales_breakdown=sales_breakdown,reports=report,start_date=start_date,end_date=end_date)
                        
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        report = daily_sales_analysis(start_date,end_date)
                        sales_breakdown = day_sales_breakdown([i for i in report])
                        start_date = datetime.strptime(start_date,"%Y-%m-%d")
                        end_date = datetime.strptime(end_date,"%Y-%m-%d")
                        return render_template("sales_analysis.html",sales_breakdown=sales_breakdown,reports=report,start_date=start_date,end_date=end_date)
  



@app.route("/cashup",methods=["GET","POST"])
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
                        start_date = datetime.strptime(start_date,"%Y-%m-%d")
                        end_date = datetime.strptime(end_date,"%Y-%m-%d")
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
                        start_date = datetime.strptime(start_date,"%Y-%m-%d")
                        end_date = datetime.strptime(end_date,"%Y-%m-%d")
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
                        

                        tank_dips = get_tank_variance(start_date,end_date,tank_id)

                        return render_template("tank_variances.html",tank_dips=tank_dips,tank=tank)
                
@app.route("/sales_summary",methods=["GET","POST"])
@check_schema
@login_required
def sales_summary():
        """Sales Summary Report"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                
                if request.method =="GET":
                       
                        products = Product.query.filter_by(product_type="Fuels").all()
                        
                        return render_template("sales_summary_filter.html",products=products)
                else:
                        start_date = request.form.get("start_date")
                        end_date = request.form.get("end_date")
                        
                        product = request.form.get("product")
                        products = Product.query.filter_by(product_type="Fuels").all()
                        if product =="All":
                                tanks = Tank.query.all()
                        else:
                                tanks = Tank.query.filter_by(product_id=product).all()
                        
                        sales_summary= daily_sales_summary(tanks,start_date,end_date)
                        start_date = datetime.strptime(start_date,"%Y-%m-%d")
                        end_date = datetime.strptime(end_date,"%Y-%m-%d")
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


@app.route("/driveway",methods=["GET","POST"])
@check_schema
@login_required
def get_driveway():

        """Query Shift Driveways for a particular day """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                if request.method == "POST":
                        
                        date = request.form.get("date")
                        
                        
                        shifts = Shift.query.filter(Shift.date == date).all()
                        return render_template("get_driveway.html",shifts=shifts,date=date)
                else:
                        
                        return render_template("get_driveway.html")
                                

@app.route("/driveway_report/<shift>",methods=["GET","POST"])
@check_schema
@login_required
def driveway_report(shift):

        """Query Shift Driveways for a particular day """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                try:
                       shift = int(shift)
                except:
                        shift = shift 
        
                if type(shift) == int:
                        
                        shift_id = shift
                        current_shift = Shift.query.get(shift_id)
                        #####
                        prev = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                        prev_shift_id=prev.id if  prev else shift_id
                        ######
                        data = get_driveway_data(shift_id,prev_shift_id)
                        date = current_shift.date
                        return render_template("driveway_report.html",avg_sales=data['avg_sales'],mnth_sales=data['mnth_sales'],lubes_daily_sale=data['lubes_daily_sale'],
                        lubes_mnth_sales=data['lubes_mnth_sales'],lube_avg=data['lube_avg'],total_lubes_shift_sales=data['total_lubes_shift_sales'],
                        products=data['products'],accounts=data['accounts'],cash_customers=data['cash_customers'],customers=data['customers'],
                        cash_up=data['cash_up'],total_cash_expenses=data['total_cash_expenses'],expenses=data['expenses'],sales_breakdown=data['sales_breakdown'],sales_breakdown_amt=data['sales_breakdom_amt'],
                        shift=current_shift,date=date,shift_daytime=current_shift.daytime,tank_dips=data['tank_dips'],pump_readings=data['pump_readings'],
                        pumps=data['pumps'],tanks=data['tanks'],total_sales_amt=data['total_sales_amt'],total_sales_ltr=data['total_sales_ltr'],product_sales_ltr=data['product_sales_ltr'])
                else:
                        #Driveway for the day
                        date = shift
                        current_shift= Shift.query.filter_by(date=date).order_by(Shift.id.desc()).first()
                        shift_id = current_shift.id
                        prev_date = current_shift.date -timedelta(days=1)
                        prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
                        if prev_shift:
                                prev_shift_id = prev_shift.id
                        else:
                                prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                                prev_shift_id = prev_shift.id if prev_shift else shift_id
                        
                        data = get_driveway_data(shift_id,prev_shift_id)
                        date = current_shift.date
                        return render_template("driveway_report.html",avg_sales=data['avg_sales'],mnth_sales=data['mnth_sales'],lubes_daily_sale=data['lubes_daily_sale'],
                        lubes_mnth_sales=data['lubes_mnth_sales'],lube_avg=data['lube_avg'],total_lubes_shift_sales=data['total_lubes_shift_sales'],
                        products=data['products'],accounts=data['accounts'],cash_customers=data['cash_customers'],customers=data['customers'],
                        cash_up=data['cash_up'],total_cash_expenses=data['total_cash_expenses'],expenses=data['expenses'],sales_breakdown=data['sales_breakdown'],sales_breakdown_amt=data['sales_breakdom_amt'],
                        shift=current_shift,date=date,shift_daytime="Total",tank_dips=data['tank_dips'],pump_readings=data['pump_readings'],
                        pumps=data['pumps'],tanks=data['tanks'],total_sales_amt=data['total_sales_amt'],total_sales_ltr=data['total_sales_ltr'],product_sales_ltr=data['product_sales_ltr'])        
                        
                

@app.route("/ss26",methods=["GET"])
@start_shift_first
@check_schema
@login_required
def ss26():

        """UPDATE DRIVEWAY DATA """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):      
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                
                #######
                shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                if shifts:
                        
                        current_shift = shifts[0]
                        prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        date = current_shift.date
                        prev_shift_id = prev_shift.id
                        data = get_driveway_data(shift_id,prev_shift_id)
                        receivable = Account.query.filter_by(account_name="Accounts Receivables").first()
                        cash_customers = Customer.query.filter(Customer.account_id != receivable.id).all()
                        ###### Cash breakdown
                        customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Customer.name != "Cash")).all()
                        credit_notes= db.session.query(Customer,CreditNote).filter(and_(Customer.id==CreditNote.customer_id,CreditNote.shift_id==shift_id,Customer.name != "Cash")).all()
                        sales_breakdown = total_customer_sales(customer_sales,credit_notes) #calculate total sales per customer)
                        sales_breakdown["Cash"] = data['total_sales_amt']- sum([sales_breakdown[i] for i in sales_breakdown])
                        
                        return render_template("ss26.html",products=data['products'],expense_accounts=data['expense_accounts'],
                        cash_accounts=data['cash_accounts'],customers=data['customers'],cash_customers=cash_customers,
                        coupons=data['coupons'],cash_up=data['cash_up'],total_cash_expenses=data['total_cash_expenses'],
                        expenses=data['expenses'],sales_breakdown=sales_breakdown,shift=current_shift,date=date,
                        shift_daytime=shift_daytime,tank_dips=data['tank_dips'],pump_readings=data['pump_readings'],suppliers=data['suppliers'],
                        pumps=data['pumps'],tanks=data['tanks'],product_sales_ltr=data['product_sales_ltr'],total_sales_amt=data['total_sales_amt'],total_sales_ltr=data['total_sales_ltr'])
                else:
                        flash("No shift started yet",'warning')
                        return redirect ('start_shift_update')



@app.route("/driveway_pump_readings",methods=["GET","POST"])
@view_only
@start_shift_first
@check_schema
@login_required
def driveway_pump_readings():


        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                if request.method =="GET":
                        shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                        if shifts:
                        
                                current_shift = shifts[0]
                                prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
                                
                                shift_id = current_shift.id
                                shift = Shift.query.get(shift_id)
                                attendants = User.query.all()
                                prev_shift_id = prev_shift.id
                                pumps = Pump.query.all()
                                pump_readings= get_pump_readings(shift_id,prev_shift_id)
                                
                                return render_template("driveway_pump_readings.html",attendants=attendants,pump_readings=pump_readings,pumps=pumps,shift=shift)
                        else:

                                flash("No shift started yet",'warning')
                                return redirect ('start_shift_update')
                else:
                        #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                        shift_id = current_shift.id
                        
                        data = request.get_json()
                        print(data)
                        pumps = Pump.query.all()
                        
                        
                        for pump in pumps:
                                l_name = "row-{}-litre".format(pump.id)
                                m_name = "row-{}-money".format(pump.id)
                                att_name = "attendant-{}".format(pump.id)
                                for i in data:
                                        if i['name'] == l_name:
                                                l_reading = i["value"]
                                        if i['name'] == m_name:
                                                m_reading = i["value"]
                                        if i['name'] == att_name:
                                                att = i["value"]
                                        
                                reading = PumpReading.query.filter(and_(PumpReading.pump_id == pump.id,PumpReading.shift_id== shift_id)).first()
                                attendant = AttendantSale(attendant_id=att,pump_id=pump.id,shift_id=shift_id)
                                litre_reading = l_reading
                                money_reading = m_reading
                                pump.litre_reading = litre_reading
                                reading.litre_reading = litre_reading
                                pump.money_reading = money_reading
                                reading.money_reading = money_reading
                                db.session.add(attendant)
                                db.session.flush()
                        db.session.commit()
                
                
                        return redirect(url_for('driveway_pump_readings'))

@app.route("/driveway_tank_dips",methods=['GET','POST'])
@view_only
@start_shift_first
@check_schema
@login_required
def driveway_tank_dips():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                if request.method =='GET':
                        shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                        if shifts:
                        
                                current_shift = shifts[0]
                                prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
                                
                                shift_id = current_shift.id
                                shift = Shift.query.get(shift_id)
                               
                                prev_shift_id = prev_shift.id
                                tanks = Tank.query.all()
                                tank_dips= get_tank_dips(shift_id,prev_shift_id)
                                suppliers = Supplier.query.all()
                                return render_template("driveway_tank_dips.html",tank_dips=tank_dips,tanks=tanks,shift=shift,suppliers=suppliers)
                        else:
                        
                                flash("No shift started yet",'warning')
                                return redirect ('start_shift_update') 
                else:

                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        data = request.get_json()
                        
                        tanks = Tank.query.all()
                        for tank in tanks:
                                d_name = "row-{}-dip".format(tank.id)
                               
                                for i in data:
                                        if i['name'] == d_name:
                                                tank_dip = i["value"]
                                shift_dip = TankDip.query.filter(and_(TankDip.tank_id == tank.id,TankDip.shift_id ==shift_id)).first()
                                shift_dip.dip = tank_dip
                                tank.dip = tank_dip
                                db.session.flush()
                        db.session.commit()
                        return redirect(url_for('driveway_tank_dips'))




@app.route("/driveway_lube_qty",methods=['GET','POST'])
@view_only
@check_schema
@login_required
def driveway_lube_qty():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                req =request.form.get("shift_id")# if the update is from  editing a previous shift
                
                if request.method=="GET":
                        shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                        if shifts:
                                current_shift = shifts[0]
                                prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
                                shift_id = current_shift.id
                                shift = Shift.query.get(shift_id)
                                prev_shift_id = prev_shift.id
                                products = Product.query.filter_by(product_type="Lubricants").order_by(Product.id.asc()).all()
                                product_sales = lube_sales(shift_id,prev_shift_id)               
                                total_sales_amt = sum([product_sales[i][2]*product_sales[i][4] for i in product_sales])
                                total_sales_ltrs = sum([product_sales[i][5]*product_sales[i][2] for i in product_sales])/1000
                                suppliers = Supplier.query.all()
                                return render_template("shift_lube_sales.html",product_sales=product_sales,shift=shift,suppliers=suppliers,products=products)
                        else:
                        
                                flash("No shift started yet",'warning')
                                return redirect ('start_shift_update')          
                else:
                                
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                        shift_id = current_shift.id
                        date = current_shift.date
                        products = Product.query.filter_by(product_type="Lubricants").order_by(Product.id.asc()).all()
                        data = request.get_json()
                        try:
                                for product in products:
                                        p_name = "row-{}-qty".format(product.id)
                               
                                        for i in data:
                                                if i['name'] == p_name:
                                                        qty = i["value"]
                                        lube_qty = LubeQty.query.filter(and_(LubeQty.shift_id==shift_id,LubeQty.product_id==product.id)).first()
                                        product.qty = qty
                                        lube_qty.qty = qty
                                        db.session.flush()
                                db.session.commit()
                               
                        except:
                                db.session.rollback()
                                flash("There was an error updating qty",'warning')
                                return redirect('driveway_lube_qty')
                        else:
                                flash('Done','info')
                                return redirect('driveway_lube_qty')
                            


@app.route("/product_prices",methods=['GET','POST'])
@view_only
@check_schema
@login_required
def product_prices():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                if request.method =='GET':
                        shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                        if shifts:
                        
                                current_shift = shifts[0]
                                prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
                                
                                shift_id = current_shift.id
                                shift = Shift.query.get(shift_id)
                               
                                prev_shift_id = prev_shift.id
                                products = Product.query.all()
                                product_sales_ltr = product_sales_litres(shift_id,prev_shift_id)
                                product_sales = lube_sales(shift_id,prev_shift_id)
                                return render_template("product_prices.html",product_sales_ltr=product_sales_ltr,product_sales=product_sales,products=products,shift=shift)
                        else:
                        
                                flash("No shift started yet",'warning')
                                return redirect ('start_shift_update') 
                
                        
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_id = current_shift.id
                
                products = Product.query.all()
                
                try:
                        data = request.get_json()
                        print(data)
                        for product in products:
                                sp_name = "row-{}-sp".format(product.id)
                                cp_name = "row-{}-cp".format(product.id)
                                for i in data:
                                        if i['name'] == cp_name:
                                                cost_price = i["value"]
                                        if i['name'] == sp_name:
                                                selling_price = i["value"]
                        
                                product.cost_price = cost_price
                                product.selling_price = selling_price
                                price =Price.query.filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).first()
                                price.cost_price = cost_price
                                price.selling_price = selling_price
                                db.session.flush()
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error",'warning')
                else:
                        return redirect('product_prices')


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
                pump = Pump.query.get(int(request.form.get("pump")))
                pump_id = pump.id
                litre_reading = request.form.get("litre_reading")
                #att = request.form.get("attendant")
                reading = PumpReading.query.filter(and_(PumpReading.pump_id == pump_id,PumpReading.shift_id== shift_id)).first()
                #attendant = AttendantSale(attendant_id=att,pump_id=pump_id,shift_id=shift_id)
                pump.litre_reading = litre_reading
                reading.litre_reading = litre_reading
                #db.session.add(attendant)
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
                shift_id = current_shift.id
                pump = Pump.query.filter_by(id=request.form.get("pump")).first()# get pumpid
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
                tank = Tank.query.filter_by(id=request.form.get("tank")).first()
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
             
                shift_id = current_shift.id
                tank= Tank.query.filter_by(id=request.form.get("tank")).first()
                document = request.form.get("document")
                qty = float(request.form.get("delivery"))
                supplier_id = request.form.get("supplier")
                supplier = Supplier.query.get(supplier_id)
                product = Product.query.get(tank.product_id)
                price= Price.query.filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).first()
                cr = supplier.account_id
                dr = product.account_id
                cost_price = float(request.form.get("cost_price"))
                amount = cost_price * qty
                new_cost = ((product.avg_price*product.qty) + amount)/(qty +product.qty)
                product.cost_price = cost_price
                product.avg_price = round(new_cost,2)
                price.avg_price = round(new_cost,2)
                price.cost_price = cost_price
                post_balance = supplier_txn_opening_balance(current_shift.date,supplier.id) + amount
                txn = SupplierTxn(date=current_shift.date,txn_type="Delivery",supplier_id=supplier.id,amount=amount,post_balance=post_balance)
                db.session.add(txn)
                db.session.flush()
                update_supplier_balances(current_shift.date,amount,supplier.id,txn.txn_type)
                delivery = Delivery(date=current_shift.date,shift_id=shift_id,tank_id=tank.id,qty=qty,product_id=tank.product_id,document_number=document,supplier=supplier_id,cost_price=cost_price,supplier_txn_id=txn.id)
                db.session.add(delivery)
                db.session.flush()
                details = "Delivery {}".format(delivery.id)
                journal = Journal(date=current_shift.date,details=details,amount=amount,dr=dr,cr=cr,created_by=session['user_id'],updated=False)
                db.session.add(journal)
                db.session.add(delivery)
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
                shift_id = current_shift.id
                product= Product.query.filter_by(id=request.form.get("product")).first()
                cost_price = float(request.form.get("cost_price"))
                price= Price.query.filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).first()
                price.cost_price = cost_price
                product.cost_price = cost_price
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
                product= Product.query.filter_by(id=request.form.get("product")).first()
                selling_price = float(request.form.get("selling_price"))
                product.selling_price = selling_price
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
                shift_id = current_shift.id
                date = current_shift.date
                vehicle_number= request.form.get("vehicle_number").capitalize()
                driver_name= request.form.get("driver_name").capitalize()
                sales_price= float(request.form.get("sales_price"))
                product_id = request.form.get("product")
                qty= float(request.form.get("qty"))
                customer_id=request.form.get("customers")
                amount= round(sales_price*qty,2)
                post_balance=customer_txn_opening_balance(date,customer_id) + amount
                txn = CustomerTxn(date=date,txn_type="Invoice",customer_id=customer_id,amount=amount,post_balance=post_balance)
                db.session.add(txn)
                db.session.flush()
                update_customer_balances(date,amount,customer_id,txn.txn_type)
                invoice = Invoice(date=date,shift_id=shift_id,product_id=product_id,customer_id=customer_id,qty=qty,price=sales_price,vehicle_number=vehicle_number,driver_name=driver_name,customer_txn_id=txn.id)
                db.session.add(invoice)
                db.session.commit()
                return redirect(url_for('ss26'))



@app.route("/driveway_invoices",methods=["GET"])
@view_only
@start_shift_first
@check_schema
@login_required
def driveway_invoices():
        """Sales Invoices"""

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                if shifts:
                        
                        current_shift = shifts[0]
                        prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
                        shift_daytime = current_shift.daytime
                        shift_id = current_shift.id
                        shift= Shift.query.all()
                        date = current_shift.date
                        prev_shift_id = prev_shift.id
                        data = get_driveway_invoices_data(shift_id,prev_shift_id)
                        receivable = Account.query.filter_by(account_name="Accounts Receivables").first()
                        cash_customers = Customer.query.filter(Customer.account_id != receivable.id).all()
                        ###### Cash breakdown
                        customer_sales= db.session.query(Customer,Invoice).filter(and_(Customer.id==Invoice.customer_id,Invoice.shift_id==shift_id,Customer.name != "Cash")).all()
                        credit_notes= db.session.query(Customer,CreditNote).filter(and_(Customer.id==CreditNote.customer_id,CreditNote.shift_id==shift_id,Customer.name != "Cash")).all()
                        sales_breakdown = total_customer_sales(customer_sales,credit_notes) #calculate total sales per customer)
                        sales_breakdown["Cash"] = data['total_sales_amt']- sum([sales_breakdown[i] for i in sales_breakdown])
                        
                        return render_template("sales_breakdown.html",products=data['products'],expense_accounts=data['expense_accounts'],
                        cash_accounts=data['cash_accounts'],customers=data['customers'],cash_customers=cash_customers,
                        coupons=data['coupons'],cash_up=data['cash_up'],total_cash_expenses=data['total_cash_expenses'],
                        expenses=data['expenses'],sales_breakdown=sales_breakdown,shift=shift,
                        product_sales_ltr=data['product_sales_ltr'],total_sales_amt=data['total_sales_amt'],total_sales_ltr=data['total_sales_ltr'])
                else:
                        flash("No shift started yet",'warning')
                        return redirect ('start_shift_update')
                return render_template('sales_breakdown.html')

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
                customer = Customer.query.filter_by(id=account).first()
                try:
                        cash_account = Account.query.filter_by(id=customer.account_id).first()
                        amount= float(request.form.get("amount"))
                        post_balance=customer_txn_opening_balance(date,customer.id) - amount
                        txn = CustomerTxn(date=date,txn_type="Payment",customer_id=customer.id,amount=amount,post_balance=post_balance)
                        db.session.add(txn)
                        db.session.flush()
                        update_customer_balances(date,amount,customer.id,txn.txn_type)
                        payment = CustomerPayments(date=date,customer_id=customer.id,amount=amount,ref=str(shift_id),customer_txn_id=txn.id)
                        receipt = SaleReceipt(date=date,shift_id=shift_id,account_id=cash_account.id,amount=amount)
                except:
                        flash("Create Customer with the same name as cash account",'warning')
                        return redirect(url_for('ss26'))
                else:
                        db.session.add(receipt)
                        db.session.add(payment)
                        cash_sales(amount,customer.id,shift_id,date)# add invoices to cash customer account
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
                total_litres = float(coupon.coupon_qty) * float(number_of_coupons)
                customer = Customer.query.get(coupon.customer_id)
                price = Price.query.filter(and_(Price.shift_id==shift_id,Price.product_id==product.id)).first()
                coupon_sale = CouponSale(date=date,shift_id=shift_id,product_id=product.id,coupon_id=coupon.id,qty=number_of_coupons)
                amount = round(total_litres * price.selling_price,2)
                post_balance=customer_txn_opening_balance(date,customer.id) +amount
                txn = CustomerTxn(date=date,txn_type="Coupon Sales",customer_id=customer.id,amount=amount,post_balance=post_balance)
                db.session.add(txn)
                db.session.flush()
                update_customer_balances(date,amount,customer.id,txn.txn_type)
                invoice = Invoice(date=date,product_id=product.id,shift_id=shift_id,customer_id=customer.id,qty=total_litres,price=price.selling_price,customer_txn_id=txn.id)
        
                db.session.add(coupon_sale)
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
                shifts = Shift.query.all()
                shift_underway = Shift_Underway.query.all()
                current_shift = shift_underway[0].current_shift
                current_shift = Shift.query.get(current_shift)
                shift_id = current_shift.id
                date = current_shift.date
                customer = Customer.query.filter_by(name="Cash").first()
                account = Account.query.get(customer.account_id)
                expected_amount = float(request.form.get("expected_amount"))
                cash_sales_amount = float(request.form.get("cash_sales_amount"))
                actual_amount= float(request.form.get("actual_amount"))
                variance= float(request.form.get("variance"))
               
                amount  = cash_sales_amount
                try:
                        cash_up = CashUp(date=date,shift_id=shift_id,sales_amount=cash_sales_amount,expected_amount=expected_amount,actual_amount=actual_amount,variance=variance)
                        receipt = SaleReceipt(date=date,shift_id=shift_id,account_id=account.id,amount=amount)
                        post_balance=customer_txn_opening_balance(date,customer.id) - amount
                        txn = CustomerTxn(date=date,txn_type="Payment",customer_id=customer.id,amount=amount,post_balance=post_balance)
                        db.session.add(txn)
                        db.session.flush()
                        update_customer_balances(date,amount,customer.id,txn.txn_type)
                        payment = CustomerPayments(date=date,customer_id=customer.id,amount=amount,ref=str(shift_id),customer_txn_id=txn.id)
                        db.session.add(payment)
                        db.session.add(cash_up)
                        db.session.add(receipt)
                        db.session.flush()
                       
                        if len(shifts) > 1:
                                cash_sales(amount,customer.id,shift_id,date)# add invoices to cash customer account
                                db.session.commit()
                                flash("Cash up done",'info')
                                return redirect(url_for('ss26'))
                        else:
                                db.session.commit()
                                flash("Cash up done",'info')
                                return redirect(url_for('ss26'))
                except Exception as e:
                        db.session.rollback()
                        flash(str(e),'warning')
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
                shift_id = current_shift.id
                date = current_shift.date
                amount= request.form.get("amount")
                source_account= request.form.get("source_account")
                pay_out_account= request.form.get("pay_out_account")
                details = "Shift {} expenses".format(shift_id)
                pay_out = PayOut(source_account=source_account,pay_out_account=pay_out_account,date=date,shift_id=shift_id,amount=amount)
                journal = Journal(date=date,details=details,amount=amount,dr=pay_out_account,cr=source_account,created_by=session['user_id'],updated=False)
                db.session.add(pay_out)
                db.session.add(journal)
                db.session.commit()
        return redirect(url_for('ss26'))


@app.route("/shift_lube_sales",methods=["POST","GET"])
@view_only
@start_shift_first
@check_schema
@login_required
def shift_lube_sales():
        """LUBE SALES PER SHIFT"""
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):

                shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                current_shift = shifts[0]
                prev_shift = shifts[1] if len(shifts) > 1 else shifts[0]
                #######
                shift_id = current_shift.id
                suppliers = Supplier.query.all()
                date = current_shift.date
                daytime = current_shift.daytime
                prev_shift_id = prev_shift.id
                products = Product.query.filter_by(product_type="Lubricants").order_by(Product.id.asc()).all()
                product_sales = lube_sales(shift_id,prev_shift_id)               
                total_sales_amt = sum([product_sales[i][2]*product_sales[i][4] for i in product_sales])
                total_sales_ltrs = sum([product_sales[i][5]*product_sales[i][2] for i in product_sales])/1000
                
                return render_template("shift_lube_sales.html",product_sales=product_sales,shift_number=shift_id,
                                        date=date,shift_daytime =daytime,suppliers=suppliers,total_sales_amt=total_sales_amt,total_sales_ltrs=total_sales_ltrs,products=products)


@app.route("/stock_sheet",methods=["GET","POST"])
@check_schema
@login_required
def get_lubes_stock_sheet():

        """Query Shift Stock Sheets for Lubes for a particular day """
        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                if request.method == "POST":
                        shift_daytime = request.form.get("shift")
                        date = request.form.get("date")
                
                        if shift_daytime != "Total":
                                current_shift= Shift.query.filter(and_(Shift.date == date,Shift.daytime == shift_daytime)).first()
                                if not current_shift:
                                        flash("No Such Shift exists",'warning')
                                        return redirect(url_for('get_lubes_stock_sheet'))
                                shift_id = current_shift.id
                                daytime = current_shift.daytime
                                date = current_shift.date
                                #####
                                prev = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                                prev_shift_id=prev.id if  prev else shift_id
                                ######
                                
                                products = Product.query.filter_by(product_type="Lubricants").all()
                                product_sales = lube_sales(shift_id,prev_shift_id)               
                                total_sales_amt = sum([product_sales[i][2]*product_sales[i][4] for i in product_sales])
                                total_sales_ltrs = sum([product_sales[i][5]*product_sales[i][2] for i in product_sales])/1000
                
                                return render_template("lubes_stocksheet.html",product_sales=product_sales,shift_number=shift_id,
                                        date=date,shift_daytime =daytime,suppliers=suppliers,total_sales_amt=total_sales_amt,total_sales_ltrs=total_sales_ltrs,products=products)
                                
                        else:
                                #Driveway for the day
                                current_shift= Shift.query.filter_by(date=date).order_by(Shift.id.desc()).first()
                                if not current_shift:
                                        flash('No such shift exists','warning')
                                        return redirect(url_for('get_lubes_stock_sheet'))
                                shift_id = current_shift.id
                                date = current_shift.date
                                prev_date = current_shift.date -timedelta(days=1)
                                prev_shift = Shift.query.filter_by(date=prev_date).order_by(Shift.id.desc()).first()
                                if prev_shift:
                                        prev_shift_id = prev_shift.id
                                else:
                                        prev_shift = Shift.query.filter(Shift.id < shift_id).order_by(Shift.id.desc()).first()
                                        prev_shift_id = prev_shift.id if prev_shift else shift_id
                                daytime ="Total"
                                
                                products = Product.query.filter_by(product_type="Lubricants").all()
                                product_sales = lube_sales(shift_id,prev_shift_id)               
                                total_sales_amt = sum([product_sales[i][2]*product_sales[i][4] for i in product_sales])
                                total_sales_ltrs = sum([product_sales[i][5]*product_sales[i][2] for i in product_sales])/1000
                
                                return render_template("lubes_stocksheet.html",product_sales=product_sales,shift_number=shift_id,
                                        date=date,shift_daytime =daytime,suppliers=suppliers,total_sales_amt=total_sales_amt,total_sales_ltrs=total_sales_ltrs,products=products)
                                                
                        
                else:

                       
                        shifts = Shift.query.order_by(Shift.id.desc()).limit(2).all()
                        
                        if shifts:
                                current_shift = shifts[0]
                                prev_shift = shifts[1] if len(shifts)>1 else shifts[0]
                                shift_daytime = current_shift.daytime
                                shift_id = current_shift.id
                              
                                date = current_shift.date
                                daytime = current_shift.daytime
                                prev_shift_id = prev_shift.id
                                
                                products = Product.query.filter_by(product_type="Lubricants").all()
                                product_sales = lube_sales(shift_id,prev_shift_id)               
                                total_sales_amt = sum([product_sales[i][2]*product_sales[i][4] for i in product_sales])
                                total_sales_ltrs = sum([product_sales[i][5]*product_sales[i][2] for i in product_sales])/1000
                
                                return render_template("lubes_stocksheet.html",product_sales=product_sales,shift_number=shift_id,
                                                        date=date,shift_daytime =daytime,suppliers=suppliers,
                                                        total_sales_amt=total_sales_amt,total_sales_ltrs=total_sales_ltrs,products=products)
                                
                        else:
                                flash("No shift updated yet",'warning')
                                return redirect(url_for('start_shift_update'))



@app.route("/update_lube_qty",methods=['POST'])
@view_only
@check_schema
@login_required
def update_lube_qty():

        with db.session.connection(execution_options={"schema_translate_map":{"tenant":session['schema']}}):
                #current_shift = Shift.query.order_by(Shift.id.desc()).first()
                req =request.form.get("shift_id")# if the update is from  editing a previous shift
                product = Product.query.filter_by(id=request.form.get("product")).first() 
                if req:
                        current_shift = Shift.query.get(req)
                        shift_id = current_shift.id
                        date = current_shift.date
                        product_qty = LubeQty.query.filter(and_(LubeQty.shift_id==current_shift.id,LubeQty.product_id==product.id)).first()
                        if product_qty:
                                try:
                                        product_qty.qty = request.form.get("qty")
                                        product.qty = request.form.get("qty")
                                        db.session.commit()
                                        return redirect(url_for('readings_entry'))
                                except:
                                        db.session.rollback()
                                        flash("There was an error",'warning')
                                        return redirect(url_for('readings_entry'))
                                        
                                        
                        else:
                                qty =request.form.get("qty")
                                lube_qty = LubeQty(shift_id=shift_id,date=date,qty=qty,product_id=product.id)
                                product.qty = request.form.get("qty")
                                try:
                                        db.session.add(lube_qty)
                                        db.session.commit()
                                        return redirect(url_for('readings_entry'))
                                except:
                                        db.session.rollback()
                                        flash("There was an error",'warning')
                                        return redirect(url_for('readings_entry'))
                                        
                                        
                else:
                                
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                        shift_id = current_shift.id
                        date = current_shift.date
                        
                        try:
                                lube_qty = LubeQty.query.filter(and_(LubeQty.shift_id==shift_id,LubeQty.product_id==product.id)).first()
                                product.qty = request.form.get("qty")
                                lube_qty.qty = request.form.get("qty")
                                db.session.commit()
                               
                        except:
                                db.session.rollback()
                                flash("There was an error updating qty",'warning')
                                return redirect('shift_lube_sales')
                        else:
                                flash('Done','info')
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
                        shift_id = current_shift.id
                        date = current_shift.date
                        try:
                                product = Product.query.filter_by(id=request.form.get("product")).first() 
                                product = LubeQty.query.filter(and_(LubeQty.shift_id==current_shift.id,LubeQty.product_id==product.id)).first()
                                product.delivery_qty = request.form.get("qty")
                                db.session.commit()
                                return redirect('readings_entry')
                        except:
                                db.session.rollback()
                                flash("There was an error",'warning')
                                return redirect('readings_entry')
                                
                else:
                                
                        shift_underway = Shift_Underway.query.all()
                        current_shift = shift_underway[0].current_shift
                        current_shift = Shift.query.get(current_shift)
                        shift_id = current_shift.id
                        date = current_shift.date

                        try:
                                product = Product.query.filter_by(id=request.form.get("product")).first() 
                                qty =float(request.form.get("qty"))
                                cost_price = float(request.form.get("cost_price"))
                                price= Price.query.filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).first()
                                product.cost_price = cost_price
                                amount = cost_price * qty
                                new_cost = ((product.avg_price*product.qty) + amount)/(qty +product.qty)
                                product.avg_price = round(new_cost,2)
                                price.cost_price = cost_price
                                price.avg_price = round(new_cost,2)
                                supplier_id = request.form.get("supplier")
                                supplier = Supplier.query.get(supplier_id)
                                document = request.form.get("document")
                                inventory = Account.query.get(product.account_id)
                                post_balance = supplier_txn_opening_balance(date,supplier.id) + amount
                                txn = SupplierTxn(date=current_shift.date,txn_type="Delivery",supplier_id=supplier.id,amount=amount,post_balance=post_balance)
                                db.session.add(txn)
                                db.session.flush()
                                update_supplier_balances(current_shift.date,amount,supplier.id,txn.txn_type)
                                delivery = Delivery(date=current_shift.date,shift_id=shift_id,qty=qty,product_id=product.id,document_number=document,supplier=supplier.id,cost_price=cost_price,supplier_txn_id=txn.id)
                                db.session.add(delivery)
                                db.session.flush()
                                details ="Delivery {}".format(delivery.id)
                                journal = Journal(date=date,details=details,amount=amount,dr=inventory.id,cr=supplier.account_id,created_by=session['user_id'],updated=False)
                                db.session.add(delivery)
                                db.session.add(journal)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash("There was an error",'warning')
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
                        shift_id = current_shift.id
                
                product = Product.query.filter_by(id=request.form.get("product")).first() 
                try:
                        cost_price = request.form.get("cost_price")
                        product.cost_price = cost_price
                        price =Price.query.filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).first()
                        price.cost_price = cost_price
                        db.session.commit()
                except:
                        db.session.rollback()
                        flash("There was an error",'warning')
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
                        shift_id = current_shift.id
                product = Product.query.filter_by(id=request.form.get("product")).first() 
                try:
                        selling_price = request.form.get("selling_price")
                        product.selling_price = selling_price
                        price =Price.query.filter(and_(Price.product_id == product.id,Price.shift_id ==shift_id)).first()
                        price.selling_price = selling_price
                        db.session.commit()
                except :
                        db.session.rollback()
                        flash('Something is wrong','warning')
                        return redirect('shift_lube_sales')
                else:
                        flash('Success','info')
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
                expected_amount = float(request.form.get("expected_amount")) or 0
                variance = cash_sales_amount-expected_amount
                check_cash_up = LubesCashUp.query.filter_by(shift_id=shift_id).first()
                if not check_cash_up:
                        cash_up = LubesCashUp(date=date,shift_id=shift_id,sales_amount=expected_amount,expected_amount=expected_amount,actual_amount=cash_sales_amount,variance=variance)
                        
                        try:
                                db.session.add(cash_up)
                                db.session.commit()
                        except:
                                db.session.rollback()
                                flash("There was an error",'warning')
                                return redirect(url_for('shift_lube_sales'))

                        else:
                                
                                flash("Cash up for Lubricants done",'info')
                                return redirect(url_for('end_shift_update'))
                else:
                        flash("Cash up for Lubricants already done",'info')
                        return redirect(url_for('end_shift_update'))


@app.route("/forgotpassword/",methods=['GET','POST'])
def forgot_password():
        """ Reset Password for Admin"""
        session.clear()
        if request.method == "GET":
                return render_template("forgot_password.html")
        else:
                
                username=request.form.get("name")
                code = request.form.get("code")
                tenant = Tenant.query.filter_by(tenant_code=code).first()
                

                if tenant:
                        session["schema"]= tenant.schema
                        session["username"] =username
                        return redirect(url_for('send_password',tenant=tenant.schema,username=username))
                else:
                        flash("Check your details and try again",'warning')
                        return redirect(url_for('login'))


@app.route("/send_password/<tenant>/<username>",methods=['GET','POST'])
def send_password(tenant,username):
        """ Send Password for Admin"""
        if request.method == "GET":
                return render_template("send_password.html")
        else:  
                with db.session.connection(execution_options={"schema_translate_map":{"tenant":tenant}}):
                        org = Tenant.query.filter_by(schema=tenant).first()
                        email = org.company_email
                        user = User.query.filter_by(username=username).first()
                        password = get_random_string()
                        hash_password = generate_password_hash(password)
                        user.password = hash_password
                        msg_body = "<h3>Please find your login details :</h3><body><p>Company Code: {}</p><p>User Name: {}</p><p>Password: {}</p><small>Make sure to change your password once logged in</small></body>".format(org.tenant_code,user.username,password)
                        msg = Message(
                        subject="Password Reset-Edriveway",
                        html=msg_body,
                        sender="kudasystems@gmail.com",
                        recipients=[email])
                        mail.send(msg)
                        
                        db.session.commit()
                        flash("Check your admin's email inbox",'info')
                        return redirect(url_for('login'))

@app.errorhandler(500)
def internal_app_error(error):

        return render_template('error.html'),500

@app.errorhandler(404)
def page_not_found(error):
        
        return render_template('404.html'),404

@app.route("/admin",methods=['GET','POST'])
@system_admin_required
def developer():
        """ Developer  Adminstration"""
        if request.method == "GET":
                tenants = Tenant.query.all()
                packages = Package.query.all()
                return render_template("admin.html",tenants=tenants,packages=packages)
        else:
                package_id = request.form.get("package")
                package = Package.query.get(package_id)
                tenant_id = request.form.get("tenant")
                tenant = Tenant.query.get(tenant_id)
                tenant.active = date.today() + timedelta(days=int(package.number_of_days))
                db.session.commit()
                return redirect(url_for('developer'))

@app.route("/developer_login",methods=['GET','POST'])
def developer_login():
        """Developer Login"""
        if request.method == "GET":
                
                return render_template("admin_login.html")
        else:
                name = request.form.get("name")
                password = request.form.get("password")
                user = SystemAdmin.query.filter_by(name=name).first()
                if user:
                        if  not check_password_hash(user.password,password):
                                flash("Wrong Password",'warning')
                                return redirect(url_for('developer_login'))
                        else:
                                session["system_admin"]= user.id
                                return redirect(url_for('developer'))
                else:
                        return redirect(url_for('index'))

@app.route("/developer_logout",methods=['GET'])
@system_admin_required
def developer_logout():
        """Developer Logout"""

        session.clear()
        
        return redirect(url_for('developer_login'))