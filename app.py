# app.py
from flask import Flask, render_template,redirect,url_for,request,redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from flask import jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    Userid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password= db.Column(db.String(128), nullable=False)


@app.route('/')
def user_index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    # Check if admin is logged in
    if 'user_id' in session:
        # Get the current admin from the database
        user_id = session['user_id']
        current_user = User.query.get(user_id)
        return render_template('dashboard.html', current_user=current_user)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error message
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if user and user.password == password:
            session['user_id'] = user.Userid
            return redirect(url_for('dashboard'))
        else:
            if not user:
                flash('Username not found. Please try again.')
            else:
                flash('Incorrect password. Please try again.')
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None  # Initialize error message
    if request.method == 'POST':
        username = request.form['username']
        email=request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
        elif User.query.filter_by(email=email).first() is not None:
            flash('Email address already exists. Please use a different one.', 'error')
        else:
            new_user = User(username=username,email=email,password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST' or request.method == 'GET':
        session.pop('user_id', None)
        return render_template('logout_success.html')

@app.route('/logout/success')
def logout_success():
    return render_template('logout_success.html')

class PersonalInformation(db.Model):
    PersonalInfoID = db.Column(db.Integer, primary_key=True)
    UserID=db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    Fname=db.Column(db.String(100), nullable=False)
    Lname=db.Column(db.String(100), nullable=False)
    DOB=db.Column(db.Date, nullable=False)
    Address=db.Column(db.String(255), nullable=False)
    Phn=db.Column(db.String(20), nullable=False)
    Email=db.Column(db.String(100), nullable=False)
    LinkedIn=db.Column(db.String(255))
    Summary=db.Column(db.Text)

class CV(db.Model):
    CV_ID=db.Column(db.Integer,primary_key=True)
    UserID=db.Column(db.Integer,db.ForeignKey('users.UserID'),nullable=False)
    Title=db.Column(db.String(255),nullable=False)
    CreationDate=db.Column(db.DateTime ,nullable=False,default=datetime.utcnow)

class Education(db.Model):
    Edu_ID=db.Column(db.Integer,primary_key=True)
    UserID=db.Column(db.Integer,db.ForeignKey('users.UserID'),nullable=False)
    Degree=db.Column(db.String(255),nullable=False)
    School=db.Column(db.String(255),nullable=False)
    FieldofStudy=db.Column(db.String(255),nullable=False)
    Grad_date=db.Column(db.Date,nullable=True)
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)