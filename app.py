from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import func
import sqlite3


app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cvbuilder.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Admin(db.Model):
    Adminid=db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)

class User(db.Model):
    Userid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)


@app.route("/")
def user_index():
    return redirect(url_for("home"))


@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/features")
def home():
    return render_template("features.html")


@app.route("/adminlogin", methods=["GET", "POST"])
def adminlogin():
    error = None  # Initialize error message
    if request.method == "POST":
        email= request.form["email"]
        password = request.form["password"]
        admin = Admin.query.filter(
            (Admin.email ==email)
        ).first()
        if admin and admin.password == password:
            session["admin_id"] = admin.Adminid
            return redirect(url_for("admindashboard"))
        else:
            if not admin:
                flash("Admin not found. Please try again.")
            else:
                flash("Incorrect password. Please try again.")
    return render_template("adminlogin.html", error=error)

@app.route("/admindashboard")
def admindashboard():
    if "admin_id" in session:
        user_id = session["admin_id"]
        current_admin = Admin.query.get(user_id)
        if current_admin:
            return render_template("dashboard.html", current_admin=current_admin)
    return redirect(url_for("adminlogin"))


@app.route("/adminregister", methods=["GET", "POST"])
def adminregister():
    error = None  # Initialize error message
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if Admin.query.filter_by(email=email).first() is not None:
            flash("Email address already exists. Please use a different one.", "error")
        else:
            new_admin = Admin(email=email,password=password)
            db.session.add(new_admin)
            db.session.commit()
            flash("Registration successful!", "success")
            return redirect(url_for("Adminlogin"))
    return render_template("adminregister.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None  # Initialize error message
    if request.method == "POST":
        username_or_email = request.form["username_or_email"]
        password = request.form["password"]
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        if user and user.password == password:
            session["user_id"] = user.Userid
            return redirect(url_for("dashboard"))
        else:
            if not user:
                flash("Username not found. Please try again.")
            else:
                flash("Incorrect password. Please try again.")
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None  # Initialize error message
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose a different one.")
        elif User.query.filter_by(email=email).first() is not None:
            flash("Email address already exists. Please use a different one.", "error")
        else:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!", "success")
            return redirect(url_for("login"))
    return render_template("register.html", error=error)

@app.route('/signin_layout')
def signin_layout():
    return render_template('signin_layout.html')


@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == "POST" or request.method == "GET":
        session.pop("user_id", None)
        return render_template("logout_success.html")


@app.route("/logout/success")
def logout_success():
    return render_template("logout_success.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" in session:
        user_id = session["user_id"]
        current_user = User.query.get(user_id)
        if current_user:
            return render_template("dashboard.html", current_user=current_user)
    return redirect(url_for("login"))


class PersonalInformation(db.Model):
    PersonalInfoID = db.Column(db.Integer, primary_key=True)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    CV_ID = db.Column(
        db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False
    )  # New column for CV ID
    Fname = db.Column(db.String(100), nullable=False)
    Lname = db.Column(db.String(100), nullable=False)
    DOB = db.Column(db.Date, nullable=False)
    Address = db.Column(db.String(255), nullable=False)
    Phn = db.Column(db.String(20), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    LinkedIn = db.Column(db.String(255))
    Summary = db.Column(db.Text)


@app.route("/submit_personal_info", methods=["POST"])
def submit_personal_info():
    if request.method == "POST":
        if "user_id" not in session:
            return "User not logged in"

        # Retrieve user ID from session
        user_id = session["user_id"]
        if "cv_id" not in session:
            return "CV not selected"
        cv_id = session["cv_id"]
        CV_ID = (cv_id,)  # Include CV ID
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        dob = func.date(request.form["dob"])
        address = request.form["address"]
        phone = request.form["phone"]
        email = request.form["email"]
        linkedin = request.form["linkedin"]
        summary = request.form["summary"]

        # Create a new instance of PersonalInformation model
        new_personal_info = PersonalInformation(
            Userid=user_id,
            CV_ID=cv_id,  # Include CV ID
            Fname=first_name,
            Lname=last_name,
            DOB=dob,
            Address=address,
            Phn=phone,
            Email=email,
            LinkedIn=linkedin,
            Summary=summary,
        )
        db.session.add(new_personal_info)
        db.session.commit()

        return render_template("education.html")


class CV(db.Model):
    CV_ID = db.Column(db.Integer, primary_key=True)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    Title = db.Column(db.String(255), nullable=False)


@app.route("/create_cv", methods=["GET", "POST"])
def create_cv():
    if request.method == "POST":
        if "user_id" not in session:
            return "User not logged in"

        # Retrieve user ID from session
        user_id = session["user_id"]
        title = request.form["title"]
        new_cv = CV(Userid=user_id, Title=title)
        db.session.add(new_cv)
        db.session.commit()
        session["cv_id"] = new_cv.CV_ID
        return render_template("personalinfo.html")
    return render_template("create_cv.html")


class Education(db.Model):
    Edu_ID = db.Column(db.Integer, primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    Degree = db.Column(db.String(255), nullable=False)
    School = db.Column(db.String(255), nullable=False)
    FieldofStudy = db.Column(db.String(255), nullable=False)
    Grad_date = db.Column(db.Date, nullable=True)


@app.route("/submit_education", methods=["POST"])
def submit_education():
    if request.method == "POST":
        if "user_id" not in session:
            return "User not logged in"

        # Retrieve user ID from session
        user_id = session["user_id"]
        if "cv_id" not in session:
            return "CV not selected"
        cv_id = session["cv_id"]
        education_details = []
        for i in range(len(request.form.getlist("degree"))):
            degree = request.form.getlist("degree")[i]
            school = request.form.getlist("school")[i]
            field_of_study = request.form.getlist("field_of_study")[i]
            graduation_date = func.date(request.form.getlist("graduation_date")[i])

            education_details.append(
                {
                    "degree": degree,
                    "school": school,
                    "field_of_study": field_of_study,
                    "graduation_date": graduation_date,
                }
            )

            # Create a new instance of Education model for each set of education details
            new_ed = Education(
                Userid=user_id,
                CV_ID=cv_id,
                Degree=degree,
                School=school,
                FieldofStudy=field_of_study,
                Grad_date=graduation_date,
            )
            db.session.add(new_ed)

        # Commit changes to the database
        db.session.commit()

        # Redirect to another page
        return render_template("Skills.html")


class Language(db.Model):
    CV_ID = db.Column(db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False)
    LanguageID = db.Column(db.Integer, primary_key=True)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    LangName = db.Column(db.String(100), nullable=False)
    Proficiency_Lang = db.Column(db.String(50), nullable=False)


# Flask route for handling language form submission
@app.route("/add_language", methods=["POST"])
def add_language():
    if request.method == "POST":
        if "user_id" not in session:
            return "User not logged in"

        # Retrieve user ID from session
        user_id = session["user_id"]
        if "cv_id" not in session:
            return "CV not selected"

        # Retrieve cv id from session
        cv_id = session["cv_id"]
        user_id = session["user_id"]
        # Retrieve language details from the form
        lang_details = []
        lang_names = request.form.getlist("lang_name")
        proficiency_levels = request.form.getlist("proficiency_Level")

        for lang_name, proficiency_level in zip(lang_names, proficiency_levels):
            # Create a new instance of Language model
            new_language = Language(
                Userid=user_id,
                CV_ID=cv_id,
                LangName=lang_name,
                Proficiency_Lang=proficiency_level,
            )

            # Add and commit the new instance to the database
            db.session.add(new_language)

        db.session.commit()

        return render_template("interest.html")


class Interest(db.Model):
    CV_ID = db.Column(db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False)
    InterestID = db.Column(db.Integer, primary_key=True)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    interest_name = db.Column(db.String(255), nullable=False)


@app.route("/add_interest", methods=["POST"])
def add_interest():
    if request.method == "POST":
        if "user_id" not in session:
            return "User not logged in"

        # Retrieve user ID from session
        user_id = session["user_id"]
        if "cv_id" not in session:
            return "CV not selected"

        # Retrieve cv id and user id from session
        cv_id = session["cv_id"]
        user_id = session["user_id"]

        # Add more interests
        interest_names = request.form.getlist("interest_name")

        for interest_name in interest_names:
            # Create a new instance of Interest model
            new_interest = Interest(
                Userid=user_id, CV_ID=cv_id, interest_name=interest_name
            )

            # Add the new interest instance to the database session
            db.session.add(new_interest)

        # Commit changes to the database
        db.session.commit()
        # skills = Skills.query.all()

        return render_template("achievement.html")


class Achievement(db.Model):
    CV_ID = db.Column(db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False)
    AchievID = db.Column(db.Integer, primary_key=True)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    desc = db.Column(db.String(255), nullable=False)


@app.route("/add_achievement", methods=["POST"])
def add_achievement():
    if request.method == "POST":
        if "user_id" not in session:
            return "User not logged in"

        # Retrieve user ID from session
        user_id = session["user_id"]
        if "cv_id" not in session:
            return "CV not selected"

        # Retrieve cv id and user id from session
        cv_id = session["cv_id"]
        # Add more interests
        achievement_names = request.form.getlist("achievement_name")

        for achievement_name in achievement_names:
            # Create a new instance of Interest model
            new_achievement = Achievement(
                Userid=user_id, CV_ID=cv_id, desc=achievement_name
            )

            # Add the new interest instance to the database session
            db.session.add(new_achievement)

        # Commit changes to the database
        db.session.commit()
        return render_template("certificate.html")


class Experience(db.Model):
    __tablename__ = "experience"
    ExpID = db.Column(db.Integer, primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    current_job = db.Column(db.Boolean, default=False)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)  # Renamed from Location
    start_date = db.Column(db.Date, nullable=False)  # Renamed from StartDate
    end_date = db.Column(db.Date, nullable=True)  # Renamed from EndDate
    description = db.Column(db.String(255), nullable=False)  # Renamed from Desc
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.SkillID"))


class Skills(db.Model):
    __tablename__ = "skills"
    SkillID = db.Column(db.Integer, primary_key=True)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    CV_ID = db.Column(db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False)
    skill_name = db.Column(db.String(255), nullable=False)  # Renamed from Skillname
    proficiency = db.Column(db.String(255), nullable=False)


class ExperienceSkills(db.Model):
    __tablename__ = "experience_skills"
    ExperienceID = db.Column(
        db.Integer, db.ForeignKey("experience.ExpID"), primary_key=True
    )
    SkillID = db.Column(db.Integer, db.ForeignKey("skills.SkillID"), primary_key=True)


@app.route("/submit_experience", methods=["POST"])
def submit_experience():
    if "user_id" not in session:
        return "User not logged in"

    # Retrieve user ID from session
    user_id = session["user_id"]
    if "cv_id" not in session:
        return "CV not selected"

    cv_id = session["cv_id"]
    experiences = []

    # Get the length of form data based on any one field
    form_length = len(request.form.getlist("title"))

    # Retrieve form data for each experience
    for i in range(form_length):
        title = request.form.getlist("title")[i]
        company = request.form.getlist("company")[i]
        location = request.form.getlist("location")[i]
        start_date_str = request.form.getlist("start_date")[i]
        end_date_str = (
            request.form.getlist("end_date")[i] if "end_date" in request.form else None
        )
        description = request.form.getlist("description")[i]
        current_job = (
            "current_job" in request.form
            and request.form.getlist("current_job")[i] == "yes"
        )
        selected_skills = request.form.getlist("selected_skills[]")

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        )

        skill_ids = ",".join(selected_skills)
        # Create a new Experience instance
        experience = Experience(
            Userid=user_id,
            CV_ID=cv_id,
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            description=description,
            current_job=current_job,
            skill_id=skill_ids,
        )

    # Add all experiences to the database and commit
    db.session.add(experience)
    db.session.commit()

    skills = Skills.query.filter_by(CV_ID=cv_id).all()
    return render_template("project.html", skills=skills)


# Flask route to handle skill addition
@app.route("/add_skill", methods=["GET", "POST"])
def add_skill():
    if request.method == "POST":
        if "user_id" not in session:
            return "User not logged in"

        # Retrieve user ID from session
        user_id = session["user_id"]
        if "cv_id" not in session:
            return "CV not selected"

        # Retrieve CV ID from the session
        cv_id = session["cv_id"]

        # Get the list of skill names and proficiency levels from the form
        skill_names = request.form.getlist("skill_name")
        proficiency_levels = request.form.getlist("proficiency_level")

        # Iterate through the submitted skill names and proficiency levels
        for skill_name, proficiency_level in zip(skill_names, proficiency_levels):
            # Create a new Skills instance for each skill
            skill = Skills(
                Userid=user_id,
                CV_ID=cv_id,
                skill_name=skill_name,
                proficiency=proficiency_level,
            )
            db.session.add(skill)

        # Commit all the new skills to the database
        db.session.commit()

        skills = Skills.query.filter_by(CV_ID=cv_id).all()
        # Redirect to a success page or render a template
        return render_template("Experience.html", skills=skills)

    # If request method is not POST (GET request), render the skill entry form
    return render_template("skills.html")


class Project(db.Model):
    ProjectID = db.Column(db.Integer, primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.SkillID"))
    PrjtName = db.Column(db.String(255), nullable=False)
    Desc = db.Column(db.String(255), nullable=False)
    Responsibilities = db.Column(db.String(255), nullable=False)


@app.route("/submit_project", methods=["POST"])
def submit_project():
    if "user_id" not in session:
        return "User not logged in"

    # Retrieve user ID from session
    user_id = session["user_id"]
    if "cv_id" not in session:
        return "CV not selected"

    cv_id = session["cv_id"]
    projects = []

    # Get the length of form data based on any one field
    form_length = len(request.form.getlist("name"))

    # Retrieve form data for each project
    for i in range(form_length):
        name = request.form.getlist("name")[i]
        description = request.form.getlist("description")[i]
        responsibilities = request.form.getlist("responsibilities")[i]
        selected_skills = request.form.getlist("selected_skills[]")

        skill_ids = ",".join(selected_skills)

        # Create a new Project instance
        project = Project(
            Userid=user_id,
            CV_ID=cv_id,
            PrjtName=name,
            Desc=description,
            Responsibilities=responsibilities,
            skill_id=skill_ids,
        )

        # Add the project to the list
        projects.append(project)

    # Add all projects to the database and commit
    db.session.add_all(projects)
    db.session.commit()

    return render_template("language.html")

app.route('/faq')
def faq():
    return render_template("faq.html")

class Certificates(db.Model):
    CertificateID = db.Column(db.Integer, primary_key=True)
    CV_ID = db.Column(db.Integer, db.ForeignKey("cv.CV_ID"), nullable=False)
    Userid = db.Column(db.Integer, db.ForeignKey("user.Userid"), nullable=False)
    Name = db.Column(db.String(255), nullable=False)
    Issuer = db.Column(db.String(255), nullable=False)


@app.route("/submit_certificate", methods=["POST"])
def submit_certificate():
    if "user_id" not in session:
        return "User not logged in"

    # Retrieve user ID from session
    user_id = session["user_id"]
    if "cv_id" not in session:
        return "CV not selected"

    cv_id = session["cv_id"]
    certificates = []
    form_length = len(request.form.getlist("name"))
    for i in range(form_length):
        name = request.form.getlist("name")[i]
        issuer = request.form.getlist("issuer")[i]
        certificate = Certificates(
            Userid=user_id, CV_ID=cv_id, Name=name, Issuer=issuer
        )
        certificates.append(certificate)

    db.session.add_all(certificates)
    db.session.commit()

    return redirect(url_for("cv_template"))


@app.route("/cv_template")
def cv_template():
    if "cv_id" not in session:
        return "CV not selected"

    cv_id = session["cv_id"]

    # Fetch user, personal information, education, experience, skills, projects, languages, interests, achievements, and certificates based on the CV ID
    user = User.query.join(CV).filter(CV.CV_ID == cv_id).first()
    personal_info = PersonalInformation.query.filter_by(CV_ID=cv_id).first()
    education = Education.query.filter_by(CV_ID=cv_id).all()
    experience = Experience.query.filter_by(CV_ID=cv_id).all()
    skills = Skills.query.filter_by(CV_ID=cv_id).all()
    projects = Project.query.filter_by(CV_ID=cv_id).all()
    languages = Language.query.filter_by(CV_ID=cv_id).all()
    interests = Interest.query.filter_by(CV_ID=cv_id).all()
    achievements = Achievement.query.filter_by(CV_ID=cv_id).all()
    certificates = Certificates.query.filter_by(CV_ID=cv_id).all()

    # Render the CV template with the fetched data
    return render_template(
        "CV.html",
        user=user,
        personal_info=personal_info,
        education=education,
        experience=experience,
        skills=skills,
        projects=projects,
        languages=languages,
        interests=interests,
        achievements=achievements,
        certificates=certificates,
    )


# QUERIES:--->


@app.route("/queryall/<int:cv_id>")
def queryall(cv_id):
    personal_info = PersonalInformation.query.filter_by(CV_ID=cv_id).all()
    education_details = Education.query.filter_by(CV_ID=cv_id).all()
    # Experience_details = Experience.query.filter_by(CV_ID=cv_id).all()
    Skill_details = Skills.query.filter_by(CV_ID=cv_id).all()
    Certificates_details = Certificates.query.filter_by(CV_ID=cv_id).all()
    interest_details = Interest.query.filter_by(CV_ID=cv_id).all()
    language_details = Language.query.filter_by(CV_ID=cv_id).all()
    Achievement_details = Achievement.query.filter_by(CV_ID=cv_id).all()
    experiences = Experience.query.filter_by(CV_ID=cv_id).all()

    # Fetch skill names associated with each experience
    experience_skills = {}
    for experience in experiences:
        skill_ids = [
            experience.skill_id
        ]  # Assuming skill_id is a comma-separated string of skill IDs
        skill_names = [
            skill.skill_name
            for skill in Skills.query.filter(Skills.SkillID.in_(skill_ids))
        ]
        experience_skills[experience.ExpID] = skill_names

    projects = Project.query.filter_by(CV_ID=cv_id).all()

    # Fetch skill names associated with each project
    project_skills = {}
    for project in projects:
        skill_ids = [
            project.skill_id
        ]  # Assuming skill_id is a comma-separated string of skill IDs
        skill_names = [
            skill.skill_name
            for skill in Skills.query.filter(Skills.SkillID.in_(skill_ids))
        ]
        project_skills[project.ProjectID] = skill_names

    return render_template(
        "Queries_all.html",
        Certificates_details=Certificates_details,
        personal_info=personal_info,
        education_details=education_details,
        experiences=experiences,
        experience_skills=experience_skills,
        Skill_details=Skill_details,
        projects=projects,
        project_skills=project_skills,
        interest_details=interest_details,
        language_details=language_details,
        Achievement_details=Achievement_details,
    )


@app.route("/display_data")
def display_data():
    # Query 1: Retrieve Users with their CV Titles and Personal Information
    users_with_cv_personal_info = (
        db.session.query(
            User,
            CV.Title,
            PersonalInformation.Fname,
            PersonalInformation.Lname,
            PersonalInformation.DOB,
            PersonalInformation.Address,
            PersonalInformation.Phn,
            PersonalInformation.Email,
            PersonalInformation.LinkedIn,
            PersonalInformation.Summary,
        )
        .join(CV, User.Userid == CV.Userid)
        .join(PersonalInformation, CV.CV_ID == PersonalInformation.CV_ID)
        .all()
    )

    # Query 2: Retrieve Users with Experience in a Specific Skill (e.g., C++)
    users_with_specific_skill_experience = (
        db.session.query(User)
        .join(CV, User.Userid == CV.Userid)
        .join(Experience, CV.CV_ID == Experience.CV_ID)
        .join(Skills, Experience.skill_id == Skills.SkillID)
        .filter(Skills.skill_name == "C++")
        .distinct(User.Userid)
        .all()
    )

    # Query 3: Retrieve Projects with Associated Skills and Users
    projects_with_skills_and_users = (
        db.session.query(Project, Skills.skill_name, User.username, User.email)
        .join(Skills, Project.skill_id == Skills.SkillID)
        .join(CV, Project.CV_ID == CV.CV_ID)
        .join(User, CV.Userid == User.Userid)
        .all()
    )

    # Query 4: Retrieve Users with Interests, Languages, and Achievements
    user_interests_languages_achievements = (
        db.session.query(
            User,
            Interest.interest_name,
            Language.LangName,
            Language.Proficiency_Lang,
            Achievement.desc,
        )
        .join(CV, User.Userid == CV.Userid, isouter=True)
        .join(Interest, CV.CV_ID == Interest.CV_ID, isouter=True)
        .join(Language, CV.CV_ID == Language.CV_ID, isouter=True)
        .join(Achievement, CV.CV_ID == Achievement.CV_ID, isouter=True)
        .all()
    )

    # Query 5: Retrieve Users with Experience in Both Python and JavaScript
    users_with_multiple_skills_experience = (
        db.session.query(User)
        .join(CV, User.Userid == CV.Userid)
        .join(Experience, CV.CV_ID == Experience.CV_ID)
        .join(Skills, Experience.skill_id == Skills.SkillID)
        .filter(Skills.skill_name.in_(["Python", "JavaScript"]))
        .group_by(User.Userid)
        .having(db.func.count(db.distinct(Skills.SkillID)) == 2)
        .all()
    )

    return render_template(
        "display_data.html",
        users_with_cv_personal_info=users_with_cv_personal_info,
        users_with_specific_skill_experience=users_with_specific_skill_experience,
        projects_with_skills_and_users=projects_with_skills_and_users,
        user_interests_languages_achievements=user_interests_languages_achievements,
        users_with_multiple_skills_experience=users_with_multiple_skills_experience,
    )


queries = [
    "SELECT u.username, e.Degree, e.School, e.FieldofStudy, e.Grad_date FROM User as u JOIN Education as e ON u.Userid = e.Userid ORDER BY e.Grad_date DESC",
    "SELECT u.username FROM User as u JOIN Skills s ON u.Userid = s.Userid JOIN Project as p ON u.Userid = p.Userid WHERE s.skill_name = 'Python' AND p.Desc LIKE '%web development%'",
    "SELECT DISTINCT u.username FROM User as u JOIN Skills as s ON u.Userid = s.Userid WHERE s.skill_name = 'Python' AND s.proficiency = 'Advanced'",
    "SELECT DISTINCT u.username FROM User u JOIN Experience e ON u.Userid = e.Userid JOIN Skills s ON u.Userid = s.Userid WHERE s.skill_name = 'Java'",
    "SELECT DISTINCT u.username FROM User u JOIN Skills s ON u.Userid = s.Userid JOIN Experience e ON u.Userid = e.Userid WHERE s.skill_name = 'Programming' AND s.proficiency = 'Advanced' AND e.title = 'Software Developer'",
    "SELECT DISTINCT u.username FROM User u JOIN Experience e ON u.Userid = e.Userid JOIN Skills s ON u.Userid = s.Userid WHERE e.title = 'Project Manager' AND s.skill_name = 'Agile Scrum'",
    "SELECT DISTINCT u.username FROM User u JOIN Interest i ON u.Userid = i.Userid WHERE i.interest_name = 'Photography'",
    "SELECT DISTINCT u.username FROM User u JOIN Skills s ON u.Userid = s.Userid JOIN Experience e ON u.Userid = e.Userid WHERE s.skill_name = 'Programming' AND s.proficiency = 'Intermediate' AND e.current_job = 1 AND e.title = 'Software Developer'",
    "SELECT DISTINCT u.username FROM User u JOIN Skills s ON u.Userid = s.Userid JOIN Education ed ON u.Userid = ed.Userid WHERE s.skill_name = 'Programming' AND s.proficiency = 'Advanced' AND ed.FieldofStudy = 'Computer Science'",
    "SELECT DISTINCT u.username FROM User u JOIN Skills s ON u.Userid = s.Userid WHERE s.skill_name = 'Programming' AND s.proficiency = 'Advanced'",
    "SELECT DISTINCT u.username,u.email FROM User u JOIN Experience e ON u.Userid = e.Userid WHERE e.location = 'New York'",
    "SELECT DISTINCT u.username,ed.Degree,ed.School FROM User u JOIN Education ed ON u.Userid = ed.Userid WHERE ed.FieldofStudy = 'Computer Science'",
    "SELECT DISTINCT u.username,e.company,s.skill_name FROM User u JOIN Skills s ON u.Userid = s.Userid JOIN Experience e ON u.Userid = e.Userid WHERE s.skill_name = 'Programming' AND s.proficiency = 'Advanced' AND e.title LIKE '%Software%'",
    "SELECT DISTINCT u.username FROM User u JOIN Education ed ON u.Userid = ed.Userid WHERE ed.FieldofStudy IN ('Computer Science', 'Information Technology')",
    "SELECT DISTINCT u.username FROM User u JOIN Skills s ON u.Userid = s.Userid JOIN Experience e ON u.Userid = e.Userid WHERE s.skill_name = 'Programming' AND s.proficiency = 'Advanced' AND e.title LIKE '%Software%' AND e.location = 'Los Angeles'",
    "SELECT DISTINCT u.username FROM User u JOIN Experience e ON u.Userid = e.Userid WHERE e.current_job = 1 AND (e.title = 'Software Developer' OR e.title = 'Java Developer')",
    "SELECT u.username, e.Degree, e.School, e.FieldofStudy, MAX(e.Grad_date) AS Latest_Graduation_Date FROM User AS u JOIN Education AS e ON u.Userid = e.Userid GROUP BY u.username",
    "SELECT u.username, COUNT(p.ProjectID) AS Project_Count FROM User AS u JOIN Project AS p ON u.Userid = p.Userid GROUP BY u.username ORDER BY Project_Count DESC LIMIT 5",
    "SELECT u.username, MAX(julianday(e.end_date) - julianday(e.start_date)) AS Longest_Experience_Duration FROM User AS u JOIN Experience AS e ON u.Userid = e.Userid GROUP BY u.username ORDER BY Longest_Experience_Duration DESC LIMIT 5",
    "SELECT u.username, s.skill_name, COUNT(s.skill_name) AS Skill_Count FROM User AS u JOIN Skills AS s ON u.Userid = s.Userid GROUP BY u.username, s.skill_name ORDER BY Skill_Count DESC LIMIT 5",
    "SELECT u.username, MAX(e.Degree) AS Highest_Education_Level FROM User AS u JOIN Education AS e ON u.Userid = e.Userid GROUP BY u.username",
    "SELECT AVG(strftime('%Y', 'now') - strftime('%Y', p.DOB)) AS Avg_Age FROM personal_information AS p",
    "SELECT u.username, p.PrjtName, p.Responsibilities, p.Desc FROM User u JOIN Project p ON u.Userid = p.Userid WHERE p.ProjectID = (SELECT MAX(ProjectID) FROM Project WHERE Userid = u.Userid)",
    "SELECT u.username, COUNT(DISTINCT s.skill_name) AS Unique_Skills FROM User u JOIN Skills s ON u.Userid = s.Userid GROUP BY u.username ORDER BY Unique_Skills DESC;",
    "SELECT (SELECT COUNT(*) FROM User) AS Total_Users,(SELECT COUNT(*) FROM CV) AS Total_CVs;"





]
query_names = [
    "1. Retrieve Education Details ordered by Graduation Date",
    "2. Retrieve Users with Python Skills and Web Development Projects",
    "3. Query to Retrieve Users with Advanced Programming Skills",
    "4. Query to Retrieve Users with Experience in Java",
    "5. Query to Retrieve Users with Advanced Programming Skills and Experience in Java",
    "6. Query to Retrieve Users with Project Management Experience and Proficiency in Agile Scrum",
    "7. Query to Retrieve Users with Interests in Photography",
    "8. Query to Retrieve Users with Intermediate Programming Skills and Current Job as Software Developer",
    "9. Query to Retrieve Users with Advanced Programming Skills and Education in Computer Science",
    "10. Query to Retrieve Users with Advanced Programming Skills",
    "11. Query to Retrieve Users with Experience in New York",
    "12. Query to Retrieve Users with Education in Computer Science",
    "13. Query to Retrieve Users with Advanced Programming Skills and Experience in Software Development",
    "14. Query to Retrieve Users with Education in Computer Science or Information Technology",
    "15. Query to Retrieve Users with Advanced Programming Skills and Experience in Software Development in Los Angeles",
    "16. Query to Retrieve Users with Current Job as Software Developer or Java Developer",
    "17. Query to Retrieve Users with the Most Recent Education Details:",
    "18. Query to Retrieve Users with the Highest Number of Projects",
    "19. Query to Find Users with the Longest Experience Duration",
    "20. Query to Retrieve Users with the Most Common Skill Name",
    "21. Query to Retrieve Users with the Highest Education Level",
    "22. Query to Calculate the Average Age of Users",
    "23. Retrieve Users with the Most Recent Project",
    "24. Retrieve Users with the Most Varied Skillset",
    "25. Query to count the number of users and CVs in the database"


]


@app.route("/custom")
def custom_query():
    answers = []
    connection = sqlite3.connect("./instance/cvbuilder.db")
    cursor = connection.cursor()
    for index, query in enumerate(queries):
        cursor.execute(query)
        resRows = cursor.fetchall()
        answers.append((query_names[index], resRows))
    connection.close()
    return render_template("custom.html", data=answers)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
