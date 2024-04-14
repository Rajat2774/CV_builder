from flask import Flask, render_template,redirect,url_for,request,redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import func

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
    if 'user_id' in session:
        user_id = session['user_id']
        current_user = User.query.get(user_id)
        if current_user:
            return render_template('dashboard.html', current_user=current_user)
    return redirect(url_for('login'))

class PersonalInformation(db.Model):
    PersonalInfoID = db.Column(db.Integer, primary_key=True)
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
        if 'cv_id' not in session:
            return 'CV not selected'
        cv_id = session['cv_id']
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
        cv_id = session['cv_id']
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
        return render_template('Skills.html')

class Language(db.Model):
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    LanguageID = db.Column(db.Integer, primary_key=True)
    Userid = db.Column(db.Integer, db.ForeignKey('user.Userid'), nullable=False)
    LangName = db.Column(db.String(100), nullable=False)
    Proficiency_Lang = db.Column(db.String(50), nullable=False)

# Flask route for handling language form submission
@app.route("/add_language", methods=['POST'])
def add_language():
    if request.method == 'POST':
        if 'cv_id' not in session:
            return 'CV not selected'
        
        # Retrieve cv id from session
        cv_id = session['cv_id']
        user_id = session['user_id']
        # Retrieve language details from the form
        lang_details = []
        lang_names = request.form.getlist('lang_name')
        proficiency_levels = request.form.getlist('proficiency_Level')

        for lang_name, proficiency_level in zip(lang_names, proficiency_levels):
            # Create a new instance of Language model
            new_language = Language(
                Userid=user_id,
                CV_ID=cv_id,
                LangName=lang_name,
                Proficiency_Lang=proficiency_level
            )

            # Add and commit the new instance to the database
            db.session.add(new_language)
        
        db.session.commit()

        return render_template('interest.html')


class Interest(db.Model):
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    InterestID = db.Column(db.Integer, primary_key=True)
    Userid = db.Column(db.Integer, db.ForeignKey('user.Userid'), nullable=False)
    interest_name = db.Column(db.String(255), nullable=False)

@app.route("/add_interest", methods=['POST'])
def add_interest():
    if request.method == 'POST':
        if 'cv_id' not in session:
            return 'CV not selected'
        
        # Retrieve cv id and user id from session
        cv_id = session['cv_id']
        user_id = session['user_id']
        
        # Add more interests
        interest_names = request.form.getlist('interest_name')

        for interest_name in interest_names:
            # Create a new instance of Interest model
            new_interest = Interest(
                Userid=user_id,
                CV_ID=cv_id,
                interest_name=interest_name
            )

            # Add the new interest instance to the database session
            db.session.add(new_interest)
        

        # Commit changes to the database
        db.session.commit()
        # skills = Skills.query.all()

        return render_template("achievement.html")



class Achievement(db.Model):
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    AchievID=db.Column(db.Integer,primary_key=True)
    desc=db.Column(db.String(255),nullable=False)

@app.route("/add_achievement",methods=['POST'])
def add_achievement():
    if request.method == 'POST':
        if 'cv_id' not in session:
            return 'CV not selected'
        
        # Retrieve cv id and user id from session
        cv_id = session['cv_id']
        # Add more interests
        achievement_names = request.form.getlist('achievement_name')

        for achievement_name in achievement_names:
            # Create a new instance of Interest model
            new_achievement = Achievement(
                CV_ID=cv_id,                
                desc=achievement_name
            )

            # Add the new interest instance to the database session
            db.session.add(new_achievement)
        

        # Commit changes to the database
        db.session.commit()
        return render_template("certificate.html")



class Experience(db.Model):   
    __tablename__ = 'experience'
    ExpID = db.Column(db.Integer, primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    current_job = db.Column(db.Boolean, default=False)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)  # Renamed from Location
    start_date = db.Column(db.Date, nullable=False)  # Renamed from StartDate
    end_date = db.Column(db.Date, nullable=True)  # Renamed from EndDate
    description = db.Column(db.String(255), nullable=False)  # Renamed from Desc
    skill_id=db.Column(db.Integer,db.ForeignKey('skills.SkillID'))

class Skills(db.Model):
    __tablename__ = 'skills'
    SkillID = db.Column(db.Integer, primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    skill_name = db.Column(db.String(255), nullable=False)  # Renamed from Skillname
    proficiency = db.Column(db.String(255), nullable=False)
    
class ExperienceSkills(db.Model):
    __tablename__ = 'experience_skills'
    ExperienceID = db.Column(db.Integer, db.ForeignKey('experience.ExpID'), primary_key=True)
    SkillID = db.Column(db.Integer, db.ForeignKey('skills.SkillID'), primary_key=True)

@app.route('/submit_experience', methods=["POST"])
def submit_experience():
    if 'cv_id' not in session:
        return 'CV not selected'

    cv_id = session['cv_id']
    experiences = []

    # Get the length of form data based on any one field
    form_length = len(request.form.getlist('title'))

    # Retrieve form data for each experience
    for i in range(form_length):
        title = request.form.getlist('title')[i]
        company = request.form.getlist('company')[i]
        location = request.form.getlist('location')[i]
        start_date_str = request.form.getlist('start_date')[i]
        end_date_str = request.form.getlist('end_date')[i] if 'end_date' in request.form else None
        description = request.form.getlist('description')[i]
        current_job = 'current_job' in request.form and request.form.getlist('current_job')[i] == 'yes'
        selected_skills = request.form.getlist('selected_skills[]')

        start_date=datetime.strptime(start_date_str,'%Y-%m-%d').date()
        end_date=datetime.strptime(end_date_str,'%Y-%m-%d').date() if end_date_str else None

        skill_ids=','.join(selected_skills)
        # Create a new Experience instance
        experience = Experience(
            CV_ID=cv_id,
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            description=description,
            current_job=current_job,
            skill_id=skill_ids
        )

    # Add all experiences to the database and commit
    db.session.add(experience)
    db.session.commit()

    skills = Skills.query.all()
    return render_template("project.html",skills=skills)


# Flask route to handle skill addition
@app.route('/add_skill', methods=["GET", "POST"])
def add_skill():
    if request.method == "POST":
        if 'cv_id' not in session:
            return 'CV not selected'

        # Retrieve CV ID from the session
        cv_id = session['cv_id']

        # Get the list of skill names and proficiency levels from the form
        skill_names = request.form.getlist('skill_name')
        proficiency_levels = request.form.getlist('proficiency_level')

        # Iterate through the submitted skill names and proficiency levels
        for skill_name, proficiency_level in zip(skill_names, proficiency_levels):
            # Create a new Skills instance for each skill
            skill = Skills(CV_ID=cv_id, skill_name=skill_name, proficiency=proficiency_level)
            db.session.add(skill)

        # Commit all the new skills to the database
        db.session.commit()

        skills = Skills.query.all()
        # Redirect to a success page or render a template
        return render_template("Experience.html", skills=skills)
    
    # If request method is not POST (GET request), render the skill entry form
    return render_template('skills.html')

class Project(db.Model):
    ProjectID=db.Column(db.Integer,primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    skill_id=db.Column(db.Integer,db.ForeignKey('skills.SkillID'))
    PrjtName=db.Column(db.String(255),nullable=False)
    Desc=db.Column(db.String(255),nullable =False)
    Responsibilities=db.Column(db.String(255),nullable=False)

@app.route('/submit_project', methods=["POST"])
def submit_project():
    if 'cv_id' not in session:
        return 'CV not selected'

    cv_id = session['cv_id']
    projects = []

    # Get the length of form data based on any one field
    form_length = len(request.form.getlist('name'))

    # Retrieve form data for each project
    for i in range(form_length):
        name = request.form.getlist('name')[i]
        description = request.form.getlist('description')[i]
        responsibilities = request.form.getlist('responsibilities')[i]
        selected_skills = request.form.getlist('selected_skills[]')

        skill_ids = ','.join(selected_skills)
        
        # Create a new Project instance
        project = Project(
            CV_ID=cv_id,
            PrjtName=name,
            Desc=description,
            Responsibilities=responsibilities,
            skill_id=skill_ids
        )

        # Add the project to the list
        projects.append(project)

    # Add all projects to the database and commit
    db.session.add_all(projects)
    db.session.commit()

    return render_template("language.html")

class Certificates(db.Model):
    CertificateID=db.Column(db.Integer,primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey('cv.CV_ID'), nullable=False)
    Name=db.Column(db.String(255),nullable=False)
    Issuer=db.Column(db.String(255),nullable=False)

@app.route('/submit_certificate', methods=["POST"])
def submit_certificate():
    if 'cv_id' not in session:
        return 'CV not selected'

    cv_id = session['cv_id']
    certificates = []
    form_length = len(request.form.getlist('name'))
    for i in range(form_length):
        name = request.form.getlist('name')[i]
        issuer = request.form.getlist('issuer')[i]
        certificate = Certificates(
            CV_ID=cv_id,
            Name=name,
            Issuer=issuer
        )
        certificates.append(certificate)

    db.session.add_all(certificates)
    db.session.commit()

    return "DONE WITH THE DETAILS PART"

    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)