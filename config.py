import os

OUR_HOST=os.getenv("DB_HOST", "localhost")
OUR_DB=os.getenv("DB_DB", "conversiones")
OUR_PORT=os.getenv("DB_PORT", "5432")
OUR_USER=os.getenv("DB_USER", "miso")
OUR_PW=os.getenv("DB_PW", "miso")
OUR_SECRET=os.getenv("SECRET", "conversiones")
OUR_JWTSECRET=os.getenv("JWTSECRET", "conversiones")

DEBUG = False
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(OUR_USER, OUR_PW, OUR_HOST, OUR_PORT, OUR_DB)
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWT_SECRET_KEY = OUR_JWTSECRET
SECRET_KEY = OUR_SECRET