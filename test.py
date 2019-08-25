""" Using this to test if  parts of the code are working or to manipulate the DB"""

from sqlalchemy import create_engine,text
from sqlalchemy.orm import scoped_session, sessionmaker

DATABASE_URL ="postgres://vyltpsivhqeaun:c0bb13175e810c1dcb143e03d1dc47b2ebaf46e095d9d6dfc8979d19f6a48e14@ec2-50-16-197-244.compute-1.amazonaws.com:5432/d3ud9s5a665gva"



# Set up database
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))
db.execute("DROP TABLE test ")
db.commit()







