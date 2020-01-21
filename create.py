from flask import Flask,render_template, request
from models import *
from werkzeug.security import generate_password_hash

#DATABASE_URL ="postgres://vyltpsivhqeaun:c0bb13175e810c1dcb143e03d1dc47b2ebaf46e095d9d6dfc8979d19f6a48e14@ec2-50-16-197-244.compute-1.amazonaws.com:5432/d3ud9s5a665gva"
POSTGRES = {
   'user': 'postgres',
   'pw':'1234',
   'db':'ss26',
   'host':'localhost',
   'port':'5432' 
}
#DATABASE_URL ="postgres://%(user)s:\%(pw)s@%(host)s:%(port)s/%(db)s"%POSTGRES
DATABASE_URL= "postgres://localhost/ss26"  
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL #os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    db.create_all()
    admin_role = Role(name = "Admin")
    db.session.add(admin_role)
    db.session.commit()
    supervisor_role = Role(name="Supervisor")
    db.session.add(supervisor_role)
    db.session.commit()
    admin_password = generate_password_hash("Eneti")
    admin = User(username="Admin",password=admin_password,role_id=1)
    db.session.add(admin)
    db.session.commit()
    shift_state = Shift_Underway(state=False)
    db.session.add(shift_state)
    db.session.commit()
if __name__=="__main__":
    with app.app_context():
        main()