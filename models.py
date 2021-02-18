from flask_sqlalchemy import SQLAlchemy
from datetime import date,datetime
from sqlalchemy import create_engine,MetaData,TIMESTAMP

metadata = MetaData(schema='tenant')
db = SQLAlchemy(metadata=metadata)


class Tenant(db.Model):
    __tablename__="tenants"
   
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String,nullable=False,unique=True)
    address =  db.Column(db.String,nullable=False)
    company_email =db.Column(db.String,nullable=False)
    database_url = db.Column(db.String,nullable=False)
    tenant_code = db.Column(db.String,nullable=False,default="0")
    contact_person = db.Column(db.String,nullable=True)
    phone_number = db.Column(db.String,nullable=True)
    schema = db.Column(db.String,nullable=True,unique=True)
    active= db.Column(db.Date,nullable=False) # package expiration date
    

    __table_args__={'schema':'public'}

class SystemAdmin(db.Model):
    __tablename__="system_admin" 
   
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String,nullable=False,unique=True)
    password = db.Column(db.String,nullable=False)
    
    __table_args__={'schema':'public'}

class Subscriptions(db.Model):
    __tablename__="subscriptions" 
   
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date = db.Column(db.Date,nullable=False)
    tenant_id = db.Column(db.Integer,db.ForeignKey("public.tenants.id"),nullable=False)
    package = db.Column(db.Integer,db.ForeignKey("public.packages.id"),nullable=False)
    amount = db.Column(db.Float,nullable=True) 
    expiration_date = db.Column(db.Date,nullable=False) 
    
    __table_args__={'schema':'public'}

class Package(db.Model):
    __tablename__="packages" 
   
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String,nullable=False,unique=True) #free, monthly,yearly
    number_of_days = db.Column(db.Integer,nullable=False) 
    
    __table_args__={'schema':'public'}


class Role(db.Model):
    __tablename__="roles"
    
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name= db.Column(db.String,nullable=False)
    #users= db.relationship("User",backref="users",lazy=True)

    def __repr__(self):
        return "{}".format(self.name)
    
    __table_args__={'schema':'public'}



class User(db.Model):
    __tablename__="users"
    
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    username = db.Column(db.String,nullable=False,unique=True)
    password = db.Column(db.String,nullable=False)
    role_id = db.Column(db.Integer,db.ForeignKey("public.roles.id"),nullable=False)
    tenant_id = db.Column(db.Integer,db.ForeignKey("public.tenants.id"),nullable=False)
    schema = db.Column(db.String,nullable=False)

    def __repr__(self):
        username =self.username
        return "{}".format(username)

    __table_args__={'schema':'tenant'}



class Shift(db.Model):
    __tablename__="shift"
    
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date = db.Column(db.Date,nullable=False)
    daytime = db.Column(db.String,nullable=True)
    prepared_by =db.Column(db.String,nullable=True)

    def __repr__(self):
        return "{}".format(self.id)
    
    __table_args__={'schema': 'tenant'}


class Product(db.Model):
    __tablename__="products"
   
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String,nullable=False)
    product_type=db.Column(db.String,nullable=False)
    cost_price =  db.Column(db.Float,nullable=True)
    avg_price =  db.Column(db.Float,nullable=True)
    selling_price = db.Column(db.Float,nullable=False)
    unit = db.Column(db.Float,nullable=False)
    qty = db.Column(db.Float,nullable=False)
    account_id = db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    
    def __repr__(self):
        name =self.name
        return "{}".format(name)

    __table_args__={'schema':'tenant'}




class LubeQty(db.Model):
    __tablename__="lube_qty"
    __table_args__={'schema':'tenant'}

    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    date= db.Column(db.Date, nullable=False)
    qty = db.Column(db.Float,nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    
    
class Tank(db.Model):

    __tablename__="tanks"
   
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String,nullable=False,unique=True)
    product_id = db.Column(db.Integer,db.ForeignKey("products.id"),nullable=False)
    dip =db.Column(db.Float,nullable=False)

    def __repr__(self):
        name =self.name
        return "{}".format(name)

    __table_args__={'schema':'tenant'}


class Pump(db.Model):

    __tablename__="pumps"
    
    id = db.Column(db.Integer,primary_key =True,nullable=False)
    name= db.Column(db.String,nullable=False,unique=True)
    tank_id = db.Column(db.Integer,db.ForeignKey("tanks.id"),nullable=False)
    litre_reading = db.Column(db.Float,nullable=False)
    money_reading = db.Column(db.Float,nullable=False)

    def __repr__(self):
        
        name =self.name
        return "{}".format(name)

    __table_args__={'schema':'tenant'}
        
class PumpReading(db.Model):
    __tablename__ = "pump_readings"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    product_id = db.Column(db.Integer,db.ForeignKey("products.id"),nullable=False)
    litre_reading = db.Column(db.Float, nullable=False)
    money_reading = db.Column(db.Float,nullable=True)
    pump_id = db.Column(db.Integer, db.ForeignKey("pumps.id"), nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    
    __table_args__={'schema':'tenant'}

class TankDip(db.Model):
    __tablename__ = "tank_dips"
    
    id = db.Column(db.Integer, primary_key=True)
    date= db.Column(db.Date, nullable=False)
    dip = db.Column(db.Float,nullable=False)
    tank_id = db.Column(db.Integer, db.ForeignKey("tanks.id"), nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)

    __table_args__={'schema':'tenant'}





class Customer(db.Model):
    __tablename__="customers"
    
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name= db.Column(db.String,nullable=False)
    contact_person =db.Column(db.String,nullable=True)
    phone_number = db.Column(db.String,nullable=True)
    account_id= db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    opening_balance= db.Column(db.Float,nullable=False)

    def __repr__(self):
        return "{}".format(self.name)
    
    __table_args__={'schema':'tenant'}

class CustomerPayments(db.Model):
    __tablename__="customer_payments"
    
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer,db.ForeignKey("customers.id"),nullable=False)
    amount= db.Column(db.Float,nullable=False)
    ref = db.Column(db.String,nullable=True)
    

    def __repr__(self):
        return "{}".format(self.amount)

    __table_args__={'schema':'tenant'}

class Supplier(db.Model):
    __tablename__="supplier"
    
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name= db.Column(db.String,nullable=False)
    contact_person =db.Column(db.String,nullable=True)
    phone_number = db.Column(db.String,nullable=True)
    account_id=db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    opening_balance= db.Column(db.Float,nullable=False)

    def __repr__(self):
        return "{}".format(self.name)
    
    __table_args__={'schema':'tenant'}

class SupplierPayments(db.Model):
    __tablename__="supplier_payments"
    
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    supplier_id = db.Column(db.Integer,db.ForeignKey("supplier.id"),nullable=False)
    amount= db.Column(db.Float,nullable=False)
    ref = db.Column(db.String,nullable=True)
    

    def __repr__(self):
        return "{}".format(self.amount)

    __table_args__={'schema':'tenant'}

class Shift_Underway(db.Model):
    __tablename__="shift_underway"
   
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    state = db.Column(db.Boolean,nullable=False)
    current_shift = db.Column(db.Integer,nullable=True)

    __table_args__={'schema':'tenant'}

class Delivery(db.Model):
    __tablename__="delivery"
    __table_args__={'schema':'tenant'}
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    tank_id = db.Column(db.Integer, db.ForeignKey("tanks.id"), nullable=True)
    date= db.Column(db.Date,nullable=False)
    qty = db.Column(db.Float,nullable=False)
    cost_price = db.Column(db.Float,nullable=False)
    product_id = db.Column(db.Integer,db.ForeignKey("products.id"),nullable=True)
    document_number = db.Column(db.String,nullable=True)
    supplier = db.Column(db.Integer,db.ForeignKey("supplier.id"),nullable=False)

class DebitNote(db.Model):
    __tablename__="debit_notes"
    __table_args__={'schema':'tenant'}
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    tank_id = db.Column(db.Integer, db.ForeignKey("tanks.id"), nullable=True)
    date= db.Column(db.Date,nullable=False)
    qty = db.Column(db.Float,nullable=False)
    cost_price = db.Column(db.Float,nullable=False)
    product_id = db.Column(db.Integer,db.ForeignKey("products.id"),nullable=True)
    document_number = db.Column(db.String,nullable=True)
    supplier = db.Column(db.Integer,db.ForeignKey("supplier.id"),nullable=False)

class Invoice(db.Model):
    __tablename__="invoices"
    __table_args__={'schema':'tenant'}
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    qty = db.Column(db.Float,nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    price= db.Column(db.Float,nullable=False)
    vehicle_number = db.Column(db.String,nullable=True)
    driver_name = db.Column(db.String,nullable=True)

class CreditNote(db.Model):
    __tablename__="credit_notes"
    __table_args__={'schema':'tenant'}
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    qty = db.Column(db.Float,nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    price= db.Column(db.Float,nullable=False)
    vehicle_number = db.Column(db.String,nullable=True)
    driver_name = db.Column(db.String,nullable=True)

class Account(db.Model):
    __tablename__="accounts"
    __table_args__={'schema':'tenant'}
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    code = db.Column(db.Integer,nullable=False)
    account_name= db.Column(db.String,nullable=False)
    account_category =db.Column(db.String,nullable=False)
    entry = db.Column(db.String,nullable=False)
    

    def __repr__(self):

        return "{}".format(self.account_name)

class SaleReceipt(db.Model):
    __tablename__="sales_receipts"
    __table_args__={'schema':'tenant'}
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    account_id= db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    amount= db.Column(db.Integer,nullable=False)



class PayOut(db.Model):
    __tablename__="payouts"
    __table_args__={'schema':'tenant'}
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    amount= db.Column(db.Integer,nullable=False)
    source_account= db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    pay_out_account = db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)


class CashUp(db.Model):
    __tablename__="cash_up"
    __table_args__={'schema':'tenant'}
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    sales_amount = db.Column(db.Integer,nullable=False)
    expected_amount= db.Column(db.Integer,nullable=False) #sales- exp
    actual_amount= db.Column(db.Integer,nullable=False) # cash banked
    variance = db.Column(db.Integer,nullable=False) #expected-actual


class LubesCashUp(db.Model):
    __tablename__="lubes_cash_up"
    __table_args__={'schema':'tenant'}
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    sales_amount = db.Column(db.Integer,nullable=False)
    expected_amount= db.Column(db.Integer,nullable=False) #sales- exp
    actual_amount= db.Column(db.Integer,nullable=False) # cash banked
    variance = db.Column(db.Integer,nullable=False)


class Price(db.Model):
    __tablename__="prices"
    __table_args__={'schema':'tenant'}
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    product_id= db.Column(db.Integer,db.ForeignKey("products.id"),nullable=False)
    cost_price= db.Column(db.Float,nullable=False)
    selling_price= db.Column(db.Float,nullable=False)
    avg_price= db.Column(db.Float,nullable=False)

    
class Coupon(db.Model):
    __tablename__="coupons"
    __table_args__={'schema':'tenant'}
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String,nullable=False)
    coupon_qty = db.Column(db.Float,nullable=False)
    customer_id = db.Column(db.Integer,db.ForeignKey("customers.id"),nullable=False)

class CouponSale(db.Model):
    __tablename__="coupon_sales"
    __table_args__={'schema':'tenant'}
    id=db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer,db.ForeignKey("shift.id"),nullable=False)
    product_id= db.Column(db.Integer,db.ForeignKey("products.id"),nullable=False)
    coupon_id = db.Column(db.Integer,db.ForeignKey("coupons.id"),nullable=False)
    qty= db.Column(db.Integer,nullable=False)


class Journal(db.Model):
    __tablename__="journals"
    __table_args__={'schema':'tenant'}

    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.DateTime, nullable=False)
    details = db.Column(db.String,nullable=True)
    dr = db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    cr = db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    amount= db.Column(db.Float,nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_on =db.Column(db.DateTime, nullable=False,default=datetime.utcnow)

class Journal_Pending(db.Model):
    __tablename__="journals_pending"
    __table_args__={'schema':'tenant'}

    id = db.Column(db.Integer,primary_key=True,nullable=False)
    date= db.Column(db.DateTime, nullable=False)
    details = db.Column(db.String,nullable=True)
    dr = db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    cr = db.Column(db.Integer,db.ForeignKey("accounts.id"),nullable=False)
    amount= db.Column(db.Float,nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_on =db.Column(db.DateTime, nullable=False,default=datetime.utcnow)