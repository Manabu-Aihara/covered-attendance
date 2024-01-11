from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
