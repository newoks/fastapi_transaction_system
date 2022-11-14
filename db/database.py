from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.config import read_config

conf = read_config('config/config.yml')

SQLALCHEMY_DATABASE_URL = f"postgresql://{conf['postgres']['user']}:{conf['postgres']['password']}@{conf['postgres']['host']}:{conf['postgres']['port']}/postgres"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
