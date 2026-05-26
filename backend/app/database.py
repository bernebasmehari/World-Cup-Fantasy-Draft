from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# 1. Setup the Database Engine
#this telling the adress of my local database, the user, the password and the port (where to find the data)
engine = create_engine(os.getenv("DATABASE_URL"), echo=True)  # echo=True enables SQL query logging

# 2. Create a "SessionLocal" factory
# autoflush=False prevents automatic changes to the DB before a commit
#this is like the door it make sure we have to acctually open and close the door
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Define the Declarative Base for models
Base = declarative_base()


