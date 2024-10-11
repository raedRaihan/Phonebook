'''References
1) https://fastapi.tiangolo.com/
2) https://github.com/sumanentc/python-sample-FastAPI-application
3) https://dassum.medium.com/building-rest-apis-using-fastapi-sqlalchemy-uvicorn-8a163ccf3aa1
'''
# Import the required modules
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import re
import os
from datetime import datetime
from enum import Enum

from passlib.context import CryptContext

import sqlite3

from fastapi.requests import Request
from fastapi.responses import FileResponse
from fastapi.responses import FileResponse


security = HTTPBasic()
password_context=CryptContext(schemes=["bcrypt"], deprecated="auto")


def clearTable():

    conn = sqlite3.connect('phonebook.db')

    cursor = conn.cursor()
    cursor.execute('DELETE FROM phonebook')
    conn.commit()
    conn.close()

# we are only storing our hashed password in the database
def verify_password(plain_password,hashed_password):
    return password_context.verify(plain_password,hashed_password)

# generate password hash
def get_password_hash(password):
    return password_context.hash(password)


# Create the FastAPI app
app = FastAPI()

# Create the SQLite database engine
engine = create_engine("sqlite:///phonebook.db", echo=True)

# Create the base class for the database models
Base = declarative_base()

def getDatabase():
    conn = sqlite3.connect('caller.db')
    cursor = conn.cursor()

    sql='SELECT * FROM callers'
    cursor.execute(sql)

    rows = cursor.fetchall()

    db={}

    for row in rows:
        db[row[0].upper()]={"username":row[0],"hashed_password":row[1],"privilege":row[2]}
        
    conn.commit()
    conn.close()
    return db

def searchUserName(username):
    db=getDatabase()

    for entry in db:
        if(db[entry]["username"]==username):
                return db[entry]


@app.get("/PhoneBook/exportAudit")
async def download_Audit(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    checkCallerInDB(credentials.username,credentials.password)
    fileName="AuditLog.csv"
    if os.path.exists(fileName):
        return FileResponse(fileName, media_type="application/octet-stream", filename=fileName)
    else:
        return {"error": "File not found"}

@app.get("/PhoneBook/exportDB")
async def download_DB(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    checkCallerInDB(credentials.username,credentials.password)
    
    fileName="phonebook.db"
    if os.path.exists(fileName):
        return FileResponse(fileName, media_type="application/octet-stream", filename=fileName)
    else:
        return {"error": "File not found"}
    


# Create the PhoneBook model class
class PhoneBook(Base):
    __tablename__ = "phonebook"

    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    phone_number = Column(String)

    '''def __repr__(self):
        return f"<PhoneBook(full_name={self.full_name}, last_name={self.last_name}, phone_number={self.phone_number})>" '''

# Create the database schema
Base.metadata.create_all(engine)

# Create the session class for database operations
Session = sessionmaker(bind=engine)


class Roles(Enum):
    Read = 1
    ReadAndWrite=2

# Create the Pydantic model class for request and response data
class Person(BaseModel):
    full_name: str
    phone_number: str

class AuditType(Enum): 
    AddName = 1
    RemoveName = 2
    ListName = 3

def addAuditENtry(timeSTamp,typeOfAudit,message,username):
    fileName="AuditLog.csv"
    
    if(os.path.exists("AuditLog.csv")==False):
        with open(fileName, 'a', newline='\n') as file:
            file.write("Time Stamp(Year-Month-Day Hour:Minute:Seconds),Action Performed,User\n")

    with open(fileName, 'a', newline='\n') as file:
        if(typeOfAudit==AuditType.AddName):
            file.write(str(timeSTamp)+","+"Added User "+message+","+username+"\n")
        elif(typeOfAudit==AuditType.RemoveName):
            file.write(str(timeSTamp)+","+"Removed User "+message+","+username+"\n")
        elif(typeOfAudit==AuditType.ListName):
            file.write(str(timeSTamp)+","+"Listed Users"+","+username+"\n")



@app.post("/PhoneBook/callers")
def add_caller(username: str, password: str, privilege: int):
    conn = sqlite3.connect('caller.db')
    cursor = conn.cursor()

    HashedPassword=get_password_hash(password)
    

    if(privilege==2):
        givenPrivlege=Roles.ReadAndWrite.value
    else:
        givenPrivlege=Roles.Read.value
    
    rowToInsert=(username,HashedPassword,givenPrivlege,)
    sql="INSERT INTO callers VALUES(?,?,?)"
    cursor.execute(sql,rowToInsert)
    conn.commit()
    conn.close()
    

def checkCallerInDB(username,password):
    conn = sqlite3.connect('caller.db')
    cursor = conn.cursor()

    sql='SELECT hashedPassword FROM callers where username=?'
    cursor.execute(sql, (username,))
    results = cursor.fetchall()

    if(len(results)<1):
        raise HTTPException(status_code=403, detail="Caller not authorized to read entries")
    
    temppassword=results[0][0]

    if(verify_password(password,temppassword) == False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect username or password",headers= {"WWW-Authenticate":"Bearer"})

    conn.close()

def checkCallerPerms(credentials: HTTPBasicCredentials = Depends(security)):

    checkCallerInDB(credentials.username,credentials.password)
    
    entry=searchUserName(credentials.username)

    if(entry["privilege"]!=Roles.ReadAndWrite.value):
        raise HTTPException(status_code=403, detail="Caller not authorized to read entries")
# Define the API endpoints

@app.post("/PhoneBook/clear")
def clearDB():
    conn = sqlite3.connect('phonebook.db')

    cursor = conn.cursor()
    cursor.execute('DELETE FROM phonebook')
    conn.commit()
    conn.close()

@app.get("/PhoneBook/list")
def list_phonebook(credentials: HTTPBasicCredentials = Depends(security)):
    checkCallerInDB(credentials.username,credentials.password)
    
    # Get a new session
    session = Session()
    # Query all the records in the phonebook table
    phonebook = session.query(PhoneBook).all()

    addAuditENtry(datetime.now(),AuditType.ListName,"nothing",credentials.username)

    # Close the session
    session.close()
    # Return the list of records as JSON objects
    return phonebook

@app.post("/PhoneBook/add")
def add_person(person: Person, credentials: HTTPBasicCredentials = Depends(security)):
    
    checkCallerPerms(credentials)

    session = Session()
    # Check if the person already exists in the database by phone number
    existing_person = session.query(PhoneBook).filter_by(phone_number=person.phone_number).first()
    # If the person exists, raise an exception
    if existing_person:
        session.close()
        raise HTTPException(status_code=400, detail="Person already exists in the database")
    
    validName = r'^([A-Z]([\'][A-Z])?[a-z]+[,]?)([ ]([A-Z]([\'][A-Z])?[a-z]+))?(([ ]|[-])([A-Z]([a-z]+|[.])))?$'
    validPhone1 = r'^(([+]?([0-9][0-9][0-9]|[1-9][0-9]?[0-9]?)))?([ -.][0-9])?([ -.]?(([\(][1-9][0-9]{1,2}[\)])|[0-9]{2,3}))?[ -.]?([0-9]{3}[ -.][0-9]{4})$'
    validPhone2= r'^[0-9]{5}([.][0-9]{5})?$'
    if re.match(validName, person.full_name): #Check if regex is correct
        pass
    else:
        session.close()
        raise HTTPException(status_code=400, detail="Not a valid name, please enter a valid name")

    if re.match(validPhone1, person.phone_number) or re.match(validPhone2, person.phone_number): #Check if regex is correct
        pass
    else:
        session.close()
        raise HTTPException(status_code=400, detail="Not a phone number, please enter a valid number") 

    # Otherwise, create a new PhoneBook record and add it to the database
    new_person = PhoneBook(full_name=person.full_name, phone_number=person.phone_number)
    session.add(new_person)
    session.commit()
    addAuditENtry(datetime.now(),AuditType.AddName,person.full_name,credentials.username)
    # Close the session
    session.close()
    # Return a success message
    return {"message": "Person added successfully"}

class PersonName(BaseModel):
    full_name: str

@app.put("/PhoneBook/deleteByName")
def delete_by_name(PN: PersonName, credentials: HTTPBasicCredentials = Depends(security)):
    # Check caller's permissions
    checkCallerPerms(credentials)
    
    # Get a new session
    session = Session()
    # Query the person by name in the database
    person = session.query(PhoneBook).filter_by(full_name=PN.full_name).first()
    # If the person does not exist, raise an exception
    if not person:
        session.close()
        raise HTTPException(status_code=404, detail="Person not found in the database")
    addAuditENtry(datetime.now(),AuditType.RemoveName,person.full_name,credentials.username)
    # Otherwise, delete the person from the database
    session.delete(person)
    session.commit()
    # Close the session
    session.close()
    # Return a success message
    return {"message": "Person deleted successfully"}

class PersonNumber(BaseModel):
    phone_number: str

@app.put("/PhoneBook/deleteByNumber")
def delete_by_number(PN: PersonNumber,credentials: HTTPBasicCredentials = Depends(security)):
    # Check caller's permissions
    checkCallerPerms(credentials)

    # Get a new session
    session = Session()
    # Query the person by phone number in the database
    person = session.query(PhoneBook).filter_by(phone_number=PN.phone_number).first()
    # If the person does not exist, raise an exception
    if not person:
        session.close()
        raise HTTPException(status_code=404, detail="Person not found in the database")
    addAuditENtry(datetime.now(),AuditType.RemoveName,person.full_name,credentials.username)
    # Otherwise, delete the person from the database
    session.delete(person)
    session.commit()
    # Close the session
    session.close()
    # Return a success message
    return {"message": "Person deleted successfully"}

