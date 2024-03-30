# app.py
from flask import Flask, render_template,redirect,url_for,request,redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from flask import jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from sqlalchemy import func
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cvbuilder.db'
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

@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'user_id' in session:
        # Get the current user from the database
        user_id = session['user_id']
        current_user = User.query.get(user_id)
        if current_user:
            return render_template('dashboard.html', current_user=current_user)
    # If user is not logged in, redirect to the login page
    return redirect(url_for('login'))

class PersonalInformation(db.Model):
    PersonalInfoID = db.Column(db.Integer, primary_key=True)
    # Userid = db.Column(db.Integer, db.ForeignKey('user.Userid'), nullable=False)
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)  # New column for CV ID
    Fname = db.Column(db.String(100), nullable=False)
    Lname = db.Column(db.String(100), nullable=False)
    DOB = db.Column(db.Date, nullable=False)
    Address = db.Column(db.String(255), nullable=False)
    Phn = db.Column(db.String(20), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    LinkedIn = db.Column(db.String(255))
    Summary = db.Column(db.Text)

@app.route('/submit_personal_info', methods=['POST'])  
def submit_personal_info():
    if request.method == 'POST':
        # if 'user_id' not in session:
        #     return 'User not logged in'

        # # Retrieve user ID from session
        # user_id = session['user_id']

        # Check if CV ID is present in the session
        if 'cv_id' not in session:
            return 'CV not selected'

        # Retrieve CV ID from the session
        cv_id = session['cv_id']

        # Retrieve personal information from the form
        CV_ID=cv_id,  # Include CV ID
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        dob = func.date(request.form['dob'])
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        linkedin = request.form['linkedin']
        summary = request.form['summary']

        # Create a new instance of PersonalInformation model
        new_personal_info = PersonalInformation(
            # Userid=user_id,
            CV_ID=cv_id,  # Include CV ID
            Fname=first_name,
            Lname=last_name,
            DOB=dob,
            Address=address,
            Phn=phone,
            Email=email,
            LinkedIn=linkedin,
            Summary=summary
        )

        # Add and commit the new instance to the database
        db.session.add(new_personal_info)
        db.session.commit()

        return render_template('education.html')



class CV(db.Model):
    CV_ID=db.Column(db.Integer,primary_key=True)
    Userid=db.Column(db.Integer,db.ForeignKey('user.Userid'),nullable=False)
    Title=db.Column(db.String(255),nullable=False)

@app.route('/create_cv', methods=['GET', 'POST'])
def create_cv():
    if request.method == 'POST':
        if 'user_id' not in session:
            return 'User not logged in'

        # Retrieve user ID from session
        user_id = session['user_id']
        title = request.form['title']
        new_cv = CV(Userid=user_id, Title=title)
        db.session.add(new_cv)
        db.session.commit()
        session['cv_id'] = new_cv.CV_ID
        return render_template('personalinfo.html')
    return render_template('create_cv.html')

class Education(db.Model):
    Edu_ID=db.Column(db.Integer,primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    Degree=db.Column(db.String(255),nullable=False)
    School=db.Column(db.String(255),nullable=False)
    FieldofStudy=db.Column(db.String(255),nullable=False)
    Grad_date=db.Column(db.Date,nullable=True)

@app.route('/submit_education', methods=['POST'])
def submit_education():
    if request.method == 'POST':
        if 'cv_id' not in session:
            return 'CV not selected'

        # Retrieve CV ID from the session
        cv_id = session['cv_id']

        # Retrieve education details from the form
        education_details = []
        for i in range(len(request.form.getlist('degree'))):
            degree = request.form.getlist('degree')[i]
            school = request.form.getlist('school')[i]
            field_of_study = request.form.getlist('field_of_study')[i]
            graduation_date = func.date(request.form.getlist('graduation_date')[i])

            education_details.append({
                'degree': degree,
                'school': school,
                'field_of_study': field_of_study,
                'graduation_date': graduation_date
            })

            # Create a new instance of Education model for each set of education details
            new_ed = Education(
                CV_ID=cv_id,
                Degree=degree,
                School=school,
                FieldofStudy=field_of_study,
                Grad_date=graduation_date
            )
            db.session.add(new_ed)

        # Commit changes to the database
        db.session.commit()

        # Redirect to another page
        return render_template('Experience.html')  # Replace 'Experience.html' with the desired template

class Experience(db.Model):   
    ExpID=db.Column(db.Integer,primary_key=True)
    # Userid=db.Column(db.Integer,db.ForeignKey('user.Userid'),nullable=False)
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    title=db.Column(db.String(255),nullable=False)
    company=db.Column(db.String(255),nullable =False)
    Location=db.Column(db.String(255),nullable=False)
    StartDate=db.Column(db.Date,nullable=False)
    EndDate=db.Column(db.Date,nullable=False)
    Desc=db.Column(db.String(255),nullable=False)

@app.route('/submit_experience', methods=["GET","POST"])
def submit_experience():
    if request.method=='POST':
        if 'cv_id' not in session:
            return 'CV not selected'

        # Retrieve CV ID from the session
        cv_id = session['cv_id']
        Title=request.form['title']
        Company=request.form['company']
        Loc=request.form['location']
        start=func.date(request.form['start_date'])
        end=func.date(request.form['end_date'])
        Desc=request.form['description']

    new_exp=Experience(CV_ID=cv_id,title=Title,company=Company,Location=Loc,StartDate=start,EndDate=end,Desc=Desc)
    db.session.add(new_exp)
    db.session.commit()
    return "Experience Submitted Successfully"

# class Skills(db.Model):
#     SkillID=db.Column(db.Integer,primary_key=True)
#     Userid=db.Column(db.Integer,db.ForeignKey("user.Userid"),nullable=False)
#     Skillname=db.Column(db.String(255),nullable=False)
#     proficiency=db.Column(db.String(255),nullable=False)

# class Project(db.Model):
#     ProjectID=db.Column(db.Integer,primary_key=True)
#     Userid=db.Column(db.Integer,db.ForeignKey('user.Userid'),nullable=False)
#     PrjtName=db.Column(db.String(255),nullable=False)
#     Desc=db.Column(db.String(255),nullable =False)
#     StartDate=db.Column(db.Date,nullable=False)
#     EndDate=db.Column(db.Date,nullable=False)
#     Responsibilities=db.Column(db.String(255),nullable=False)

# class ProjectSkills(db.Model):
#     ProjectSkillID = db.Column(db.Integer, primary_key=True)
#     ProjectID = db.Column(db.Integer, db.ForeignKey('projects.CV_ID'), nullable=False)
#     SkillID = db.Column(db.Integer, db.ForeignKey('skills.SkillID'), nullable=False)

# class SkillCertificates(db.Model):
#     SkillCertificateID = db.Column(db.Integer, primary_key=True)
#     SkillID = db.Column(db.Integer, db.ForeignKey('skills.SkillID'), nullable=False)
#     CertificateID = db.Column(db.Integer, db.ForeignKey('certificates.CertificateID'), nullable=False)

# class Achievement(db.Model):
#     AchievID=db.Column(db.Integer,primary_key=True)
#     Userid=db.Column(db.Integer,db.ForeignKey("user.Userid"),nullable=False)
#     Desc=db.Column(db.String(255),nullable=False)

# class Certificates(db.Model):
#     CertificateID=db.Column(db.Integer,primary_key=True)
#     Userid=db.Column(db.Integer,db.ForeignKey("user.Userid"),nullable=False)
#     Name=db.Column(db.String(255),nullable=False)
#     Issuer=db.Column(db.String(255),nullable=False)
#     Date=db.Column(db.Date,nullable=False)

# class Language(db.Model):
#     LanguageID = db.Column(db.Integer, primary_key=True)
#     Userid = db.Column(db.Integer, db.ForeignKey('user.Userid'), nullable=False)
#     LanguageName = db.Column(db.String(100), nullable=False)
#     ProficiencyLevel = db.Column(db.String(50), nullable=False)

# class Interest(db.Model):
#     InterestID = db.Column(db.Integer, primary_key=True)
#     Userid = db.Column(db.Integer, db.ForeignKey('user.Userid'), nullable=False)
#     InterestDescription = db.Column(db.String(255), nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)