import os

from flask import Flask, session, render_template,flash,request,redirect,url_for,jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, admin_required
from models import *
app = Flask(__name__,template_folder = "templates")

# Set Database URL
#DATABASE_URL ="postgres://vyltpsivhqeaun:c0bb13175e810c1dcb143e03d1dc47b2ebaf46e095d9d6dfc8979d19f6a48e14@ec2-50-16-197-244.compute-1.amazonaws.com:5432/d3ud9s5a665gva"
DATABASE_URL ="postgres://localhost/ss26"
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.urandom(24)
db.init_app(app)


shift_underway =0 # Yes/No (1/0) keeps track of whether a shift update has started or not
current_shift_id =0 # keeps track of the current shift_id 

@app.route("/",methods=["GET","POST"])
@login_required
def index():
    """ Index"""
    #return render_template("index.html")
    return render_template("readings_entry.html",shift_underway=shift_underway)

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
                        message = "Username/Password Not Correct !!"
                        return render_template("error.html",message=message)
                else:
                        session["user_id"] = user.id
                        return redirect(url_for('index'))
        else:
                return render_template("login.html")

@app.route("/start_shift_update",methods=["GET","POST"])
@login_required
def start_shift_update():
        "Start Update of Shift Figures"
        if request.method == "POST":
                if shift_underway == 0:#check if there is a shift update going on
                        day= request.form.get("date")
                        daytime = request.form.get("daytime")
                        shift_underway = 1
                        return redirect(url_for('readings_entry'))
                else:
                        message = "Another Shift Update is Already Underway, end it first !!"
                        return render_template("error.html",message=message)
        else:
                return render_template("start_shift_update.html")

@app.route("/readings_entry",methods=["GET","POST"])
@login_required
def readings_entry():
        """Readings Entry"""
        return render_template("readings_entry.html",shift_underway=shift_underway)

@app.route("/pump_readings_entry",methods=["POST"])
@login_required
def pump_readings_entry():
        """Enter readings for pumps """   
        date = request.form.get("date")
        shift = request.form.get("shift")
        pump_name= request.form.get("pump_name")
        pump_reading =request.form.get("pump_reading")

@app.route("/tank_dips_entry",methods=["POST"])
@login_required
def tank_dips_entry():
        """Enter Dips for Tanks """   
        date = request.form.get("date")
        shift = request.form.get("shift")
        tank_name= request.form.get("tank_name")
        tank_dip =request.form.get("tank_dip")

@app.route("/fuel_delivery",methods=["POST"])
@login_required
def fuel_delivery():
        """Enter Fuel Delivery"""   
        date = request.form.get("date")
        shift = request.form.get("shift")
        document_number = request.form.get("document_number")
        tank_name= request.form.get("tank_name")
        litres =request.form.get("litres_delivered")

@app.route("/admin",methods=["GET","POST"])
@login_required
@admin_required
def admin():
        """Home page for admin functions"""
        return render_template("admin.html")

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

@app.route("/admin/manage_inventory",methods=["GET","POST"])
@login_required
@admin_required
def manage_inventory():
        """Managing Inventory Functions"""
        if request.method == "GET":

                return render_template("manageusers.html")


@app.route("/add_user",methods=["POST"])
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

@app.route("/edit_user",methods=["POST"])
@login_required
@admin_required
def edit_user():
        """Edit User Information"""
        db.session.query(User).filter(User.username == request.form.get("username")).update({User.password: generate_password_hash(request.form.get("password"))}, synchronize_session = False)
        db.session.query(User).filter(User.username == request.form.get("username")).update({User.role_id: request.form.get("role")}, synchronize_session = False)
        db.session.commit()
        flash('User Successfully Updated')
        return redirect(url_for('manage_users'))

@app.route("/delete_user",methods=["POST"])
@login_required
@admin_required
def delete_user():
        """Deletes Users"""
        user = db.session.query(User).get(int(request.form.get("users")))
        db.session.delete(user)  
        db.session.commit()
        flash('User Successfully Removed!!')
        return redirect(url_for('manage_users'))

@app.route("/add_pump",methods=["POST"])
@login_required
@admin_required
def add_pump():
        """Add Pump"""
        pump = Pump(request.form.get("pump_name"),request.form.get("tank_id"))
        db.session.add(pump)
        db.session.commit()

@app.route("/add_tank",methods=["POST"])
@login_required
@admin_required
def add_tank():
        """Add Tank"""
        tank = Pump(request.form.get("tank_name"),request.form.get("product"))
        db.session.add(tank)
        db.session.commit()

'''

@app.route("/shift_driveway",methods=["GET","POST"])
def shift_driveway():
    """Query Shift Driveways for a particular day """
    if request.method == "POST":
        date_ = request.form.get("date")
        daytime_ = request.form.get("shift")
        shift_id = Shift.query.filter(and_(Shift.date == date_,Shift.daytime= daytime_)).all()   
        prev_shift_id = int(shift_id)-1
        pump_reading = {}
        pumps = Pump.query.all()
        for pump in pumps:
                prev_shift_reading = PumpReading.query.filter(and_(PumpReading.id=prev_shift_id,PumpReading.pump_id == pumps.pump_id)).first()
                prev_shift_reading = prev_shift_reading.reading
                current_shift_reading = PumpReading.query.filter(and_(PumpReading.id=shift_id,PumpReading.pump_id == pumps.pump_id)).first()
                current_shift_reading = current_shift_reading.reading
                pump_reading[pump.name]=[prev_shift_reading,current_shift_reading]
        
@app.route("/cashup",methods=["GET","POST"])
def shift_driveway():
    """Cash ups for a particular shift"""
    if request.method == "POST":
        date = request.form.get("date")
        shift = request.form.get("shift")

@app.route("/daily_driveway",methods=["GET","POST"])
def daily_driveway():
    """Query Driveways for a particular day """
    if request.method == "POST":
        date = request.form.get("date")'''



