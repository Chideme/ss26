import os

from flask import Flask, session, render_template,flash,request,redirect,url_for,jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from models import *
app = Flask(__name__,template_folder = "templates")

# Set Database URL
DATABASE_URL ="postgres://vyltpsivhqeaun:c0bb13175e810c1dcb143e03d1dc47b2ebaf46e095d9d6dfc8979d19f6a48e14@ec2-50-16-197-244.compute-1.amazonaws.com:5432/d3ud9s5a665gva"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.urandom(24)
db.init_app(app)




@app.route("/",methods=["GET","POST"])
@login_required
def index():
    """ Index"""
    return render_template("login.html")

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
'''
@app.route("/readings_entry",methods=["GET","POST"])
def readings_entry():
    """Enter readings for pumps """
    if request.method == "POST":
        date = request.form.get("date")
        tank_id = request.form.get("tank_id")
        tank_dip = request.form.get("tank_dip")
        pump_id = pump_id
        pump_reading =request.form.get("pump_reading")


@app.route("/cashup",methods=["GET","POST"])
def shift_driveway():
    """Cash ups for a particular shift"""
    if request.method == "POST":
        date = request.form.get("date")
        shift = request.form.get("shift")


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
        


@app.route("/daily_driveway",methods=["GET","POST"])
def daily_driveway():
    """Query Driveways for a particular day """
    if request.method == "POST":
        date = request.form.get("date")'''



