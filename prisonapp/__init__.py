from flask import Flask, Blueprint, request, abort,url_for, jsonify, g, render_template, make_response,session
from flask_sqlalchemy import SQLAlchemy
import os, sqlalchemy, jwt, datetime
from flask_httpauth import HTTPBasicAuth
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_cors import CORS
from datetime import date


app = Flask(__name__)


CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:gringotts687713@localhost/prisonapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['USE_SESSION_FOR_NEXT'] = True
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'thisissecret'
app.secret_key = os.urandom(24)

db = SQLAlchemy(app)

import prisonapp.api



def createDB():
    engine = sqlalchemy.create_engine('postgresql+psycopg2://postgres:gringotts687713@localhost') #connects to server
    engine.execute("CREATE DATABASE IF NOT EXISTS prisonapp") #create db
    engine.execute("USE prisonapp") # select new

def createTables():
    db.create_all()

#createDB()
createTables()