import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, flash, url_for, session, make_response, send_from_directory, jsonify
from flask import send_file, abort
from flask_socketio import SocketIO, emit, join_room
from math import ceil
from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy import func
import os
from sqlite3 import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from collections import defaultdict
import re
import uuid
import time
import socketio

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
app.secret_key = "MmUPastPap3rs2510@CSP1123"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///mmupastpapers.db"
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['CHAT_IMG_FOLDER'] = "static/chat"
app.config['STUDENT_UPLOADS'] = "static/student_uploads"
app.config['ALLOWED_EXTENSION'] = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16MB
app.config.update({
    'PERMANENT_SESSION_LIFETIME': timedelta(days=7), #Session will expire after 7 days
    'SESSION_COOKIE_SAMESITE': 'Lax', 
    'SESSION_REFRESH_EACH_REQUEST': True #Refresh session on each request
})
db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) #Create upload folder if it doesn't exist
os.makedirs(app.config['CHAT_IMG_FOLDER'], exist_ok=True)
os.makedirs(app.config['STUDENT_UPLOADS'], exist_ok=True)

#-----------------------------------------------------------------------------------------------------------
#Create database tables  
#ENTITY: FACULTY_INFO  
class FACULTY_INFO(db.Model): 
  FACULTY_ID = db.Column(db.String(3), primary_key=True) 
  FACULTY_DESC = db.Column(db.Text, nullable=False) 

#ENTITY: USER_INFO 
class USER_INFO(db.Model):  
  USER_ID = db.Column(db.String(50), primary_key=True, unique=True) 
  USER_EMAIL = db.Column(db.String(255), unique=True) 
  NAME = db.Column(db.String(200), nullable=False) 
  PASSWORD = db.Column(db.String(255), nullable=False) 
  ROLES = db.Column(db.Integer, nullable=False) #1 indicates student; 2 indicates lecturer  
  CREATED_ON = db.Column(db.DateTime, default=datetime.now) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.now, nullable=True) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 
  FACULTY_ID = db.Column(db.String(3), db.ForeignKey(FACULTY_INFO.FACULTY_ID))
 
#ENTITY: SECURITY_QUES 
class SECURITY_QUES(db.Model): 
  SECURITY_QUES_ID = db.Column(db.String(100), primary_key=True) 
  SECURITY_QUES_DESC = db.Column(db.Text, nullable=False) 
 
#ENTITY: SECURITY_QUES_ANS 
class SECURITY_QUES_ANS(db.Model):
  USER_ID =  db.Column(db.String(50), db.ForeignKey(USER_INFO.USER_ID)) 
  SECURITY_QUES_ID = db.Column(db.String(100), db.ForeignKey(SECURITY_QUES.SECURITY_QUES_ID)) 
  ANSWER = db.Column(db.Text) 
  CREATED_ON = db.Column(db.DateTime, default=datetime.now, nullable=True) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.now, nullable=True) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 

  __table_args__ = (db.PrimaryKeyConstraint('USER_ID','SECURITY_QUES_ID'),)

#ENTITY: STUDY_LVL_INFO  
class STUDY_LVL_INFO(db.Model): 
  STUDY_LVL_ID = db.Column(db.String(4), primary_key=True) 
  STUDY_LVL_DESC = db.Column(db.Text, nullable=False) 

#ENTITY: SUBJECT_INFO  
class SUBJECT_INFO(db.Model): 
  SUBJECT_ID = db.Column(db.String(7), primary_key=True) 
  SUBJECT_DESC = db.Column(db.Text, nullable=False) 
  STUDY_LVL_ID = db.Column(db.String(4), db.ForeignKey(STUDY_LVL_INFO.STUDY_LVL_ID)) 
  FACULTY_ID = db.Column(db.String(3), db.ForeignKey(FACULTY_INFO.FACULTY_ID)) 
 
#ENTITY: TERM_INFO 
class TERM_INFO(db.Model): 
  TERM_ID = db.Column(db.Integer, primary_key=True) 
  TERM_DESC = db.Column(db.Text, nullable=False) 
   
class PASTPAPERS_INFO(db.Model): 
  PAPER_ID = db.Column(db.String(10), primary_key=True) 
  TERM_ID = db.Column(db.Integer, db.ForeignKey(TERM_INFO.TERM_ID)) 
  FILENAME = db.Column(db.Text, nullable=True) 
  FILEPATH = db.Column(db.String(255), nullable=False) 
  PAPER_DESC = db.Column(db.Text, nullable=True) 
  UPLOAD_ON = db.Column(db.DateTime, default=datetime.now) 
  UPLOAD_BY = db.Column(db.String(50), db.ForeignKey(USER_INFO.USER_ID)) 
  LAST_MODIFIED_BY = db.Column(db.String(50), db.ForeignKey(USER_INFO.USER_ID), nullable=True) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.now) 
  SUBJECT_ID = db.Column(db.String(7), db.ForeignKey(SUBJECT_INFO.SUBJECT_ID))
 
#ENTITY: CLASS 
class CLASS(db.Model): 
  CLASS_ID = db.Column(db.String(50), primary_key=True) 
  CLASS_NAME = db.Column(db.Text, nullable=False) 
  CREATED_BY = db.Column(db.String(50), nullable=False) 
  CREATED_ON = db.Column(db.DateTime, default=datetime.now) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.now) 
  SUBJECT_ID = db.Column(db.String(7), db.ForeignKey(SUBJECT_INFO.SUBJECT_ID))  
  TERM_ID = db.Column(db.Integer, db.ForeignKey(TERM_INFO.TERM_ID))  

#ENTITY: USER_CLASS 
class USER_CLASS(db.Model): 
  USER_ID = db.Column(db.String(50), db.ForeignKey(USER_INFO.USER_ID)) 
  CLASS_ID = db.Column(db.String(50), db.ForeignKey(CLASS.CLASS_ID)) 
  JOINED_AT = db.Column(db.DateTime, default=datetime.now) 

  __table_args__ = (db.PrimaryKeyConstraint('USER_ID','CLASS_ID'),)

#ENTITY: ANSWER_BOARD 
class ANSWER_BOARD(db.Model): 
  ANSWER_BOARD_ID = db.Column(db.String(50), primary_key=True) 
  PAPER_ID = db.Column(db.String(50), db.ForeignKey(PASTPAPERS_INFO.PAPER_ID)) 
  CLASS_ID = db.Column(db.String(50), db.ForeignKey(CLASS.CLASS_ID)) 
  CREATED_BY = db.Column(db.String(50), nullable=False) 
  CREATED_ON = db.Column(db.DateTime, default=datetime.now) 
  ANSWER_BOARD_NAME = db.Column(db.Text)
 
#ENTITY: ANSWER_FIELD 
class ANSWER_FIELD(db.Model): 
  ANSWER_FIELD_ID = db.Column(db.String(50), primary_key=True)
  ANSWER_FIELD_DESC = db.Column(db.Text, nullable=True) 
  ANSWER_FIELD_TYPE = db.Column(db.Integer, nullable=False) #1: Text field, 2: MCQ, 3: Upload file 
  ANSWER_BOARD_ID = db.Column(db.String(50), db.ForeignKey(ANSWER_BOARD.ANSWER_BOARD_ID))
  MCQ_TYPE = db.Column(db.Integer) #4: 4 answer options, 5: 5 answer options 

#ENTITY: ANSWER  
class ANSWER(db.Model): 
  ANSWER_ID = db.Column(db.String(50), primary_key=True)
  ANSWER_FIELD_ID = db.Column(db.String(50), db.ForeignKey(ANSWER_FIELD.ANSWER_FIELD_ID)) 
  ANSWER_BY = db.Column(db.String(50), nullable=False) 
  ANSWER_ON = db.Column(db.DateTime, default=datetime.now) 
  ANSWER_CONTENT = db.Column(db.Text) 

#ENTITY: DISCUSSION_FORUM 
class DISCUSSION_FORUM(db.Model): 
  COMMENT_ID = db.Column(db.String(100), primary_key=True) 
  COMMENT = db.Column(db.Text) 
  ANSWER_BOARD_ID = db.Column(db.String(50), db.ForeignKey(ANSWER_BOARD.ANSWER_BOARD_ID)) 
  POSTED_BY = db.Column(db.String(50), nullable=False) 
  POSTED_ON = db.Column(db.DateTime, default=datetime.now)

#ENTITY: MCQ_OPTION
class MCQ_OPTION(db.Model):
   MCQ_OPTION_ID = db.Column(db.String(50), primary_key=True)
   MCQ_OPTION_DESC = db.Column(db.Text)
   MCQ_OPTION_FLAG = db.Column(db.Integer, nullable=True)
   ANSWER_FIELD_ID = db.Column(db.String(50), db.ForeignKey(ANSWER_FIELD.ANSWER_FIELD_ID))

#ENTITY: CHAT_MESSAGE
class CHAT_MESSAGE(db.Model):
  CHAT_ID = db.Column(db.String(100), primary_key=True)
  ANSWER_BOARD_ID = db.Column(db.String(50), db.ForeignKey(ANSWER_BOARD.ANSWER_BOARD_ID))
  SENT_BY = db.Column(db.String(50), db.ForeignKey(USER_INFO.USER_ID))
  MESSAGE_CONTENT = db.Column(db.Text, nullable=True)
  IMAGE_URL = db.Column(db.String(200), nullable=True)
  TIMESTAMP = db.Column(db.DateTime, default=datetime.now)

#-------------------------------------------------------------------------------------------------------
#Finish setting up database tables 

@socketio.on('join')
def on_join(data):
    room = data['room']
    print(f"Joining room: {room}")
    join_room(room)

def isStrongPassword(password):
  pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{10,}$'
  return bool(re.match(pattern, password))

def allowed_file(filename):
   ALLOWED_EXTENSION = {'pdf'}
   return '.' in filename and filename.rsplit('.', 1)[1]. lower() in ALLOWED_EXTENSION

@app.before_request
def refresh_session():
    session.permanent = True #Set session to permanent
    app.permanent_session_lifetime = timedelta(days=7) #Set session to expire after 7 days

@app.route('/login',methods=['GET','POST'])
def login():
    status = True #Flag to determine whether user input is valid or invalid 

    if request.method == 'POST':
        #Retrive user input 
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not session.get('newRegistered'):
          session['newRegistered'] = False 
        print(email, password) #For debugging purposes 

        #Input verification 
        if not email or not password:
            flash('Email and password are required', 'error')
            status = False
            print("Email or password is empty.") #For debugging purposes
            return redirect('/login')

        
        #Retrive data from database 
        user = USER_INFO.query.filter_by(USER_EMAIL=email).first()
        print(user) #For debugging purposes
        if not user:
            flash('Invalid email.', 'error')
            status = False
            print(f"Invalid email {email}") #For debugging purposes
            print(user == email) #For debugging purposes
            return redirect('/login')
        if not check_password_hash(user.PASSWORD, password):
            flash('Invalid password', 'error')
            status = False
            print(f"Invalid password {password}") #For debugging purposes
            print(password == user.PASSWORD) #For debugging purposes
            print(check_password_hash(user.PASSWORD, password)) #For debugging purposes
            return redirect('/login')
        
        if status == True:
          print(f"User new registered ? {session.get('newRegistered')}")
          if session.get('newRegistered') is True:
            registerStatus = 1
          elif session.get('newRegistered') is False:
            registerStatus = 2
          else:
            registerStatus = 3
            session.clear()
            flash('Unknown user status. Please login properly.','error')
            print("Unknown user register status?")
            return redirect('/login')
          session['email'] = user.USER_EMAIL
          session['name'] = user.NAME
          session['roles'] = user.ROLES
          session['user_id'] = user.USER_ID
          session.permanent = True #Set session to permanent
          session['user_id'] = user.USER_ID
          flash('Login successful!', 'success')
          print(f"Login successful for user {email}.") #For debugging purposes
          pending_class = session.pop('pending_class', None)
          if pending_class:
            print("Join class logic.")
            return redirect(url_for('join_class_link', class_id=pending_class))
          else:
            print("Normal login logic.")
            return render_template('login.html',registerStatus=registerStatus)
        
    return render_template("login.html")

@app.route('/register' ,methods=['GET','POST'])
def register():
    faculties = FACULTY_INFO.query.all()
    if request.method == 'GET':
       return render_template("register.html", faculties=faculties)
    print("Executing register action")
    if request.method == 'POST':
        #Retrive user input 
        email = request.form['email'].strip()
        name = request.form['name']
        faculty_id = request.form.get['faculty']
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        roles = request.form.get('user_type')

        #Process the "roles" input 
        if roles == "student":
           rolesNum = 1
        elif roles == "lecturer":
           rolesNum = 2
        else:
           rolesNum = None

        print(f"New registration info: {email},{name},{password},{roles},{rolesNum}.") #For debugging purposes 

        #Input verification 
        if not FACULTY_INFO.query.get(faculty_id):
           flash('Invalid faculty selected', 'error')
           return redirect('/register')

        if password != confirm_password:
           flash('Passwords do not match.', 'error')
           print(f"Passwords do not match. New password:{password} vs Confirm password:{confirm_password}.") #For debugging purposes 
           return redirect('/register')
        
        if not all ([email, name, password, confirm_password, roles]):
           flash('All fields are required.', 'error')
           print("All/some fields are empty.") #For debugging purposes
           return redirect('/register')
        
        if not isStrongPassword(password):
           flash("Password must be at least 10 characters, contains at least 1 uppercase, 1 lowercase, 1 symbol and 1 digit.", "error")
           print("Password does not meet the requirements.") #For debugging purposes
           return redirect('/register')
        
        if not re.match(r"^[\w\.-]+@([\w]+\.)*mmu\.edu\.my$", email):
          flash("Please enter a valid MMU email address.", 'error')
          print("Email does not met requirement.")
          return redirect('/register')
        
        #Retrive data from database 
        user_db = USER_INFO.query.filter_by(USER_EMAIL=email).first()
        print(f"Email: {user_db}") #For debugging purposes

        #Avoid duplication of data 
        if user_db:
           flash('Email already existed.', 'error')
           return redirect('/register')
        if rolesNum == None:
           flash('Invalid option for User Type.', 'error')
           print(f"Invalid roles: {rolesNum}") #For debugging purposes
           print(f"Roles selected: {roles}") #For debugging purposes
           return redirect('/register')

        #Generate a unique user ID 
        userId = uuid.uuid4().hex[:10]
        print(userId) #For debugging purposes

        try:
           new_user = USER_INFO(USER_ID=userId, USER_EMAIL=email, NAME=name, PASSWORD=generate_password_hash(password), ROLES=rolesNum, FACULTY_ID=faculty_id)
           db.session.add(new_user)
           db.session.commit()
           flash('User registered successfully!', 'success')
           print(f"User {email} succesfully registered")
           session['newRegistered'] = True
           print(f"New registered: {session.get('newRegistered')}")
           print(f"Variable type: {type(session.get('newRegistered'))}")
           return render_template("register.html")
        except IntegrityError:
           db.session.rollback()
           flash('Email already exists.', 'error')
           print("Email already exists.")
           return redirect('/register')
        except Exception as e:
           db.session.rollback()
           flash('Error occurred while registering user. Please try again later', 'error')
           print(f"Internal server error: {e}")
           return redirect('/register')
    return render_template("register.html")

@app.route('/')
@app.route('/main')
def main():
    session.clear()
    return render_template("main.html")

@app.route('/resetPassword', methods=['GET', 'POST'])
def resetPassword():
  questions = SECURITY_QUES.query.all()
  print(datetime.now())

  if request.method == 'POST':

    #Retrive user input
    email = request.form['email']
    new_password = request.form['newPassword']
    confirm_password = request.form['confirmPassword']
    question_id = request.form['securityQuestion']
    answer = request.form['securityAnswer']

    #User input verification
    if not email or not new_password or not confirm_password or not question_id or not answer:
      flash("Please fill in all information!", "error")
      print("Please fill in all information!") #For debugging purposes
      return redirect(url_for('resetPassword'))
    
    if not isStrongPassword(new_password):
      flash("Password must be at least 10 characters, contains at least 1 uppercase, 1 lowercase, 1 symbol and 1 digit.", "error")
      print("Password does not match requirements.") #For debugging purposes
      return redirect(url_for('resetPassword'))

    if new_password != confirm_password:
      flash("Passwords do not match!", "error")
      print(f"Passwords do not match! Password: {new_password}, {confirm_password}") #For debugging purposes
      return redirect(url_for('resetPassword'))

    #Save new data into database
    #try:
    email = USER_INFO.query.filter_by(USER_EMAIL=email).first()
    print(email)

    #Use email to find user ID
    if email:
       userID = email.USER_ID
    else:
       userID = None
    print(userID)

    try:
      if email:
        record = SECURITY_QUES_ANS.query.filter_by(USER_ID=userID, SECURITY_QUES_ID=question_id, ANSWER=answer).first()
        print(record) #For debugging purposes

        if record:
          user = USER_INFO.query.filter_by(USER_ID=userID).first()
          user.PASSWORD = generate_password_hash(new_password)
          user.LAST_MODIFIED_ON = datetime.now()
          user.LAST_MODIFIED_BY = user.USER_EMAIL 
          db.session.commit()
          flash("Password reset successfully!", "success")
          print(f"Password reset sucessfully for user {email}, {question_id}, the new password is {new_password}.") #For debugging purposes
          return render_template("resetPassword.html")
        
        elif record == None:
          flash("Incorrect answer for security question. Try again.", "error")
          print(f"Incorrect answer for security question.") #For debugging purposes 
          return redirect(url_for('resetPassword'))
      
      else:
         flash("Email does not exist.", "error")
         print(f"Email {email} does not exists") #For debugging purposes 
         return redirect(url_for('resetPassword'))
    except IntegrityError:
      db.session.rollback()
      flash("Email registered!")
      return redirect(url_for('/resetPassword'))
    except Exception as e:
      db.session.rollback()
      flash("Error occurred while registering user. Please try again later", "error")
      print("Internal server error.")
      return redirect(url_for('resetPassword'))
    
  return render_template('resetPassword.html', questions=questions)

def getInitials(name):
  parts = name.strip().split()
  
  if len(parts) >= 2:
     initials = parts[0][0]+parts[1][0]
  elif len(parts) == 1:
     initials = parts[0][0]
  else:
     initials = None 
  
  return initials 

#For all html file
@app.context_processor
def inject_data():
    if session.get('email'):
      email = session.get('email')
      name = session.get('name')
      initials = getInitials(name)
      print(initials) #For debugging purposes 
      print(email)

      return {
        'email': session.get('email'),
        'name': session.get('name'),
        'roles': session.get('roles'),
        'newRegistered': session.get('newRegistered'),
        'initials': initials,
        'class_id': session.get('current_class_id')
      }
    
    else:
       return { }

@app.route('/editProfile', methods=['GET', 'POST'])
def editProfile():
  if request.method == 'POST':
    email = session.get('email')
    name = session.get('name')
    newName = request.form['name']
    print("New name: ",newName) #For debugging purposes 

    #Input verification / validation 
    if not newName or newName.strip() == '':
      flash("Name fields are required!",'error')
      print("Name fields are empty.") #For debugging purposes 
      return redirect('/editProfile') 
    
    #Retrieve data from database and compare 
    emailRecord = USER_INFO.query.filter_by(USER_EMAIL=email).first()
    if not emailRecord:
      flash('User not found.','error')
      print("User not found.") #For debugging purposes 
      return redirect('/editProfile') 
       
    #Get user ID 
    user_ID = emailRecord.USER_ID
    print("Email obtained:",email,"and respective user ID:",user_ID) #For debugging purposes

    #Get record 
    record = USER_INFO.query.filter_by(USER_ID=user_ID).first()
    print("Email + name:",record)
    try:
      if record: 
        record.NAME = newName 
        record.LAST_MODIFIED_BY = email 
        record.LAST_MODIFIED_ON = datetime.now()
        db.session.commit()
        session.clear()
        flash('Edit profile successfully! Please login again.','success')
        print("Edit profile success.") #For debugging purposes 
        return render_template('editProfile.html')
      else:
        flash('User record not found.','error')
        print("User record not found.") #For debugging purposes 
        return redirect('/editProfile')
    except Exception as e:
      flash('Error occurs while editing user profile. Please try again later.','error')
      print("Internal server error.") #For debugging purposes 
      return redirect('/editProfile')
       
  return render_template("editProfile.html")

from sqlalchemy import and_

@app.route('/view_papers')
def view_papers():
    # Get search filter inputs
    term = request.args.get('term', '').strip()
    subject = request.args.get('subject', '').strip()
    filename = request.args.get('filename', '').strip()
    description = request.args.get('description', '').strip()

    print(f"Term: {term}, Subject: {subject}, Filename: {filename}, Desc: {description}")
    page = request.args.get('page', 1, type=int)
    per_page = 5

    # Base query
    query = PASTPAPERS_INFO.query

    # Apply filters only if they are provided
    filters = []
    
    if term:
        filters.append(func.lower(PASTPAPERS_INFO.TERM_ID) == term.lower())
    if subject:
        filters.append(func.lower(PASTPAPERS_INFO.SUBJECT_ID) == subject.lower())
    if filename:
        filters.append(PASTPAPERS_INFO.FILENAME.ilike(f"%{filename}%"))
    if description:
        filters.append(PASTPAPERS_INFO.PAPER_DESC.ilike(f"%{description}%"))

    # Apply all filters with 'and_' to combine them
    if filters:
        query = query.filter(and_(*filters))

    # Debugging: Print the query to check the applied filters
    print(str(query))

    # Pagination and count
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    total_papers = query.count()

    return render_template(
        "view_papers.html",
        pastpapers_info=pagination.items,
        pagination=pagination,
        total_papers=total_papers
    )

@app.route('/view_paper/<paper_id>')
def view_paper(paper_id):
    paper = db.session.get(PASTPAPERS_INFO,paper_id)
    return send_file(paper.FILEPATH, mimetype='application/pdf')

@app.route('/download_paper/<paper_id>')
def download_paper(paper_id):
    paper = db.session.get(PASTPAPERS_INFO,paper_id)

    if paper and os.path.exists(paper.FILEPATH):
        # Add the .pdf at the end of FIlename is the original name doesn't have .pdf
        filename = paper.FILENAME
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'

        return send_file(
            paper.FILEPATH,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    else:
        abort(404, description="Paper not found or file missing.")

@app.route('/securityQues', methods=['GET', 'POST'])
def securityQues():
  print("Executing security question page...")
  #Retrieve data from database:
  email = session.get('email')

  #Get Question List 
  ques = db.session.query(SECURITY_QUES.SECURITY_QUES_ID, SECURITY_QUES.SECURITY_QUES_DESC).all()
  securityQuesList = {id: question for id, question in db.session.query(SECURITY_QUES.SECURITY_QUES_ID, SECURITY_QUES.SECURITY_QUES_DESC).all()}
  print("Security Question List:", securityQuesList) #For debugging purposes 

  #Get User ID
  emailObject = USER_INFO.query.filter_by(USER_EMAIL=email).first()
  user_ID = emailObject.USER_ID
  print("Email obtain:",email,"and respective user ID:",user_ID) #For debugging purposes 

  #Get Answers 
  answers = SECURITY_QUES_ANS.query.filter_by(USER_ID=user_ID).all()
  answer_dict = {a.SECURITY_QUES_ID: a.ANSWER for a in answers}
  print("Answer List:",answer_dict) #For debugging purposes 

  #Merge questions and ans 
  questions = SECURITY_QUES.query.all()
  user_qa = [{'id': q.SECURITY_QUES_ID, 'question': q.SECURITY_QUES_DESC, 'answer': answer_dict.get(q.SECURITY_QUES_ID, '-')} for q in questions]
  print("User Q&A List:",user_qa) #for debugging purposes 

  if session.get('newRegistered') is True:
     registerStatus = 1
  elif session.get('newRegistered') is False:
     registerStatus = 2
  else:
     registerStatus = 3

  print(f"User new register ? {session.get('newRegistered')}")
  print(f"Register status {registerStatus}")
  
  if request.method == 'POST':
      #Save data into database: 
      user_ans = request.form.to_dict()
      print("User answer list:", user_ans) #For debugging purposes 
  
      for ques_id, answer in user_ans.items():
          record = SECURITY_QUES_ANS.query.filter_by(USER_ID=user_ID, SECURITY_QUES_ID=ques_id).first()
     
          #If record exists 
          if record:
              record.ANSWER = answer
              record.LAST_MODIFIED_ON = datetime.now()
              record.LAST_MODIFIED_BY = user_ID
          else:
              newRecord = SECURITY_QUES_ANS(
                  USER_ID=user_ID,
                  SECURITY_QUES_ID=ques_id,
                  ANSWER=answer,
                  CREATED_ON=datetime.now(),
                  LAST_MODIFIED_ON=datetime.now(),
                  LAST_MODIFIED_BY=user_ID)
              db.session.add(newRecord)
     
      db.session.commit()
      if registerStatus == 2:
        flash("Security questions edited successfully! Please log in again.", 'success')
      elif registerStatus == 1:
        flash("Security questions sucessfully setup!",'success')
      print("Sucessfully saved new sec ques.") #For debugging purposes 
      return render_template("securityQues.html",registerStatus=registerStatus)
  return render_template("securityQues.html", user_qa=user_qa)

@app.route('/logout')
def logout():
   print("Executing logout action...")
   session.clear()
   flash('Logged out successfully!', 'success')
   response = make_response(render_template("showAlert.html", showAlert=True))
   response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
   return response

@app.route('/upload_paper', methods=['GET', 'POST']) 
def upload_paper():
    file = None
    filepath = None

    if 'roles' not in session or session['roles'] != 2:
        flash('Access denied: Only lecturers can upload papers', 'error')
        return redirect('/login')

    if request.method == 'POST':
        try:
            paper_desc = request.form.get('paper_desc').strip()
            term_id = request.form.get('term_id')
            subject_id = request.form.get('subject_id')  # <-- New: get subject_id from form
            file = request.files.get('file')
            upload_dir = app.config['UPLOAD_FOLDER']

            if not all([paper_desc, term_id, subject_id, file]):
                flash('All fields are required!', 'error')
                return redirect('/upload_paper')

            if not TERM_INFO.query.get(term_id):
                flash('Invalid term selected', 'error')
                return redirect('/upload_paper')
            
            if not SUBJECT_INFO.query.get(subject_id):
                flash('Invalid subject selected', 'error')
                return redirect('/upload_paper')

            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
                os.chmod(upload_dir, 0o755)

            if not allowed_file(file.filename):
                flash('Only PDF files are allowed!', 'error')
                return redirect('/upload_paper')

            orig_filename = secure_filename(file.filename)
            unique_id = uuid.uuid4().hex[:8]
            timestamp = int(time.time())
            saved_filename = f"{unique_id}_{timestamp}_{orig_filename}"
            filepath = os.path.join(upload_dir, saved_filename)
            file.save(filepath)

            new_paper = PASTPAPERS_INFO(
                PAPER_ID=uuid.uuid4().hex[:10],
                TERM_ID=term_id,
                SUBJECT_ID=subject_id,  # <-- New: Save subject_id
                FILENAME=orig_filename,
                FILEPATH=filepath,
                PAPER_DESC=paper_desc,
                UPLOAD_BY=session['user_id'],
                LAST_MODIFIED_BY=session['user_id']
            )

            db.session.add(new_paper)
            db.session.flush()
            db.session.commit()

            session.modified = True
            session['last_activity'] = datetime.now().timestamp()

            flash('Paper uploaded successfully!', 'success')
            return render_template("upload_paper.html", terms=TERM_INFO.query.all(), subjects=SUBJECT_INFO.query.all())

        except Exception as e:
            db.session.rollback()
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
            print(f"Failed to upload file: {e}")
            flash(f'Error occurred while uploading paper: {str(e)}', 'error')
            app.logger.error(f"upload error: {str(e)}", exc_info=True)
            session.setdefault('retry_count', 0)
            session['retry_count'] += 1
        return redirect(url_for('view_papers'))

    terms = TERM_INFO.query.all()
    subjects = SUBJECT_INFO.query.all()  # <-- New: get subjects
    return render_template('upload_paper.html', terms=terms, subjects=subjects)


@app.route('/delete_paper/<paper_id>', methods=['POST'])
def delete_paper(paper_id):
    paper = PASTPAPERS_INFO.query.get_or_404(paper_id)

    try:
        # Delete the file from the file system if it exists
        if paper.FILEPATH and os.path.exists(paper.FILEPATH):
            os.remove(paper.FILEPATH)

        # Delete the record from the database
        db.session.delete(paper)
        db.session.commit()
        flash('Paper deleted successfully!', 'success')
        return render_template("view_papers.html")

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting paper: {e}', 'error')

    return redirect('/view_papers')

@app.route('/view_class', methods=['GET', 'POST'])
def view_class():
    #Show Term Info in Filter Section 
    term_info = TERM_INFO.query.all()
    terms = []
    for term in term_info:
       term_dict = {
          'term_id': term.TERM_ID,
          'term_name': term.TERM_DESC
       }
       terms.append(term_dict)

    #Get pagination parameters
    term_filter = request.form.get('term') if request.method == 'POST' else request.args.get('term', 'all')
    page = int(request.args.get('page', 1)) if request.method == 'POST' else int(request.args.get('page', 1))
    entry = request.form.get('entry', 12) if request.method == 'POST' else request.args.get('entry', 12)
    per_page = int(entry)
    print(f"Term: {term_filter}, Page={page}, Entry: {entry} / {type(entry)}, Per_Page: {per_page} / {type(per_page)}")

    #Show Class Record 
    records = USER_CLASS.query.filter_by(USER_ID=session.get('user_id')).all()
    print("User class:", records)
    classIds = [record.CLASS_ID for record in records]
    print(f"Class ID under user {session.get('user_id')} : {classIds}")

    query = CLASS.query.filter(CLASS.CLASS_ID.in_(classIds))
    if term_filter and term_filter != 'all':
       query = query.filter(CLASS.TERM_ID == term_filter)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    classes = pagination.items

    class_records = []
    for cls in classes:
        lecturer = USER_INFO.query.filter_by(USER_ID=cls.CREATED_BY).first()
        class_records.append({
            'classID': cls.CLASS_ID,
            'className': cls.CLASS_NAME,
            'termID': cls.TERM_ID,
            'lecturerName': lecturer.NAME if lecturer else 'Unknown'
        })

    print("Final record:", class_records)
    return render_template("view_class.html", terms=terms, records=class_records, pagination=pagination, selected_term=term_filter, selected_entry=int(per_page))

@app.route('/open_class/<class_id>', methods=['GET','POST'])
def open_class(class_id):
   session['current_class_id'] = class_id
   class_data = CLASS.query.filter_by(CLASS_ID=class_id).first()
   if not class_data:
      message = "Class not found! Join a class?", 404
      return message
   
   answer_boards = ANSWER_BOARD.query.filter_by(CLASS_ID=class_id).all()
   print(f"Answer Board record: {answer_boards}")
   
   answer_board_info = [] 

   for answer_board in answer_boards:
      creator = USER_INFO.query.filter_by(USER_ID=answer_board.CREATED_BY).first() 
      creatorName = creator.NAME 
      
      answer_board_info.append({
         'answer_board_id': answer_board.ANSWER_BOARD_ID,
         'answer_board_name': answer_board.ANSWER_BOARD_NAME,
         'creator': creatorName
      })

   print(f"Final record Answer Board Info: {answer_board_info}")
   return render_template("class_page.html",class_data=class_data, class_id=class_id, answer_board_info=answer_board_info)

@app.route('/createClass', methods=['GET','POST'])
def createClass():
  #Show data in template
  subjectRec = db.session.query(SUBJECT_INFO.SUBJECT_ID, SUBJECT_INFO.SUBJECT_DESC).all()
  print(f"Subject list: {subjectRec}") #For debugging purposes 

  subject_list = [
     {'subject_id': subject_id, 'subject_name': subject_desc}
     for subject_id, subject_desc in subjectRec
  ]
  print(f"Subject list to be returned: {subject_list}") #For debugging purposes 

  termRec = db.session.query(TERM_INFO.TERM_ID, TERM_INFO.TERM_DESC).all()
  print(f"Term list: {termRec}") #For debugging purposes 

  term_list = [
     {'term_id': term_id, 'term_name': term_desc}
     for term_id, term_desc in termRec
  ]
  print(f"Term list to be returned: {term_list}") #For debugging purposes 

  if request.method == 'POST':
    className = request.form['className']
    subject = request.form['subject']
    term = request.form['term']

    #Input verification 
    if not className or not subject or not term:
       flash('All fields are required!','error')
       print("All/some fiedls are empty.") #For debugging purposes 
       return redirect(url_for('createClass'))
    
    #Retrieve data from database and compare 
    record = CLASS.query.filter_by(CLASS_NAME=className, SUBJECT_ID=subject, TERM_ID=term).first()
    print(f"The class record is: {record}") #For debugging purposes 

    if record: 
      db.session.rollback()
      flash('The class you want to create existed!','error')
      print("Class existed!") #For debugging purposes 
      return redirect(url_for('createClass'))
    else: #Create a new class in db 
      try: 
        classID = uuid.uuid4().hex[:6]
        new_record = CLASS(CLASS_ID=classID, CLASS_NAME=className, CREATED_BY=session.get('user_id'), SUBJECT_ID=subject, TERM_ID=term)
        new_record2 = USER_CLASS(CLASS_ID=classID, USER_ID=session.get('user_id'), JOINED_AT=datetime.now())
        db.session.add(new_record)
        db.session.add(new_record2)
        db.session.commit()
        flash('Class created successfully!','success')
        print(f"Class {className} created!") #For debugging purposes 
        return render_template("create_class.html", classCode=classID)
      except IntegrityError:
        flash('The class you want to create existed!','error')
        return redirect(url_for('createClass'))
      except Exception as e:
        flash('Error occurs while creating class. Please try again later.','error')
        print(f"Internal server error: {e}")
        return redirect(url_for('createClass'))
       
  return render_template("create_class.html", subjectList=subject_list, termList=term_list)

@app.route('/joinClass', methods=['GET','POST'])
def joinClass():

  if request.method == 'POST':
    user_id = session.get('user_id')
    classCode = request.form['classCode']
    print("Class Code from user: ",classCode) #For debugging purposes 

    #Input verification 
    if not classCode: 
      flash('Please enter a class code!','error')
      print("Empty class code received.") #For debugging purposes 
      return redirect(url_for('view_class'))
  
    #Join class action 
    classID = CLASS.query.filter_by(CLASS_ID=classCode).first()
    print("Class code from db: ",classID) #For debugging purposes 

    already_joined = USER_CLASS.query.filter_by(CLASS_ID=classCode, USER_ID=user_id).first()
    print("User already joined:",already_joined) #For debugging purposes
    try:
      #If user joined 
      if already_joined:
        flash('You joined this class!','error')
        print("User joined this class!") #For debugging purposes 
        return redirect(url_for('view_class'))
      
      #If class ID exists 
      if classID:
        new_record = USER_CLASS(USER_ID=user_id, CLASS_ID=classCode, JOINED_AT=datetime.now())
        db.session.add(new_record)
        db.session.commit()
        flash('Join class successfully!','success')
        print("Join class action success.") #For debugging purposes 
        return redirect(url_for('open_class', class_id=classCode, showAlert=False))
      
      #If class not exists 
      elif not classID:
        flash('Class not found. Please check your class code.','error')
        print("Wrong class code input.") #For debugging purposes 
        return redirect(url_for('view_class'))
    except Exception as e:
      flash('Error occurs while joining class. Please try again.','error')
      print("Internal server error.") #For debugging purposes 
      return redirect(url_for('view_class'))

  return redirect(url_for('view_class')) #In case 'GET' method is passed 

@app.route('/view_people/<class_id>')
def view_people(class_id):
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', 'all')

    class_data = CLASS.query.filter_by(CLASS_ID=class_id).first()
    if not class_data:
        abort(404, description="Class not found")

    query = db.session.query(USER_INFO).join(USER_CLASS).filter(
        USER_CLASS.CLASS_ID == class_id
    )

    if role_filter == 'students':
        query = query.filter(USER_INFO.ROLES == 1)
    elif role_filter == 'lecturers':
        query = query.filter(USER_INFO.ROLES == 2)

    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(USER_INFO.NAME.ilike(search_term))

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template(
        "view_people.html",
        class_data=class_data,
        class_id=class_id,
        pagination=pagination,
        selected_role=role_filter,
        search_query=search_query,
        total_members=query.count()
    )

@app.route('/create_answer_board/<class_id>', methods=['GET','POST'])
def create_answer_board(class_id):
   print(f"Class ID: {class_id}")
   class_info = CLASS.query.filter_by(CLASS_ID=class_id).first()
   print(class_info)
   current_subject_id = class_info.SUBJECT_ID
   print(current_subject_id)
   papers = PASTPAPERS_INFO.query.filter_by(SUBJECT_ID=current_subject_id).all()
   
   papers_record = []
   for paper in papers: 
      papers_record.append({
         'paper_id': paper.PAPER_ID,
         'term': paper.TERM_ID,
         'subject_id': paper.SUBJECT_ID
      })
   
   print(f"Final papers record: {papers_record}")

   return render_template("upload_answer_board.html", papers=papers_record)

@app.route('/upload_answer_board/<class_id>', methods=['GET','POST'])
def upload_answer_board(class_id):
   if request.method == 'POST':
      answer_board_name = request.form.get('answer_board_des')
      paper_id = request.form.get('paper')

      if not answer_board_name or not paper_id:
         flash("All fields are required!",'error')
         print("All/some fields are empty.") #For debugging purposes 
         return redirect(f"/upload_answer_board/{session.get('current_class_id')}")

      record = ANSWER_BOARD.query.filter_by(PAPER_ID=paper_id, CLASS_ID=session.get('current_class_id')).all()
      if record:
         flash("Sorry, answer_board you want to create existed!",'error')
         print("answer_board created existed.") #For debugging purposes 
         return redirect(f"/upload_answer_board/{session.get('current_class_id')}")
      else:
         try:
            answer_board_id = uuid.uuid4().hex[:8]
            new_record = ANSWER_BOARD(ANSWER_BOARD_ID=answer_board_id, PAPER_ID=paper_id, CLASS_ID=class_id, CREATED_BY=session.get('user_id'), CREATED_ON=datetime.now(), ANSWER_BOARD_NAME=answer_board_name)
            db.session.add(new_record)
            db.session.commit()
            flash("Answer board created successfully!",'success')
            print("Answer board created successfully!") #For debugging purposes 
            session['current_answer_board_id'] = answer_board_id
            return render_template("upload_answer_board.html", classCode=session.get('current_class_id'), answerBoardId=session.get('current_answer_board_id'))
         except IntegrityError:
            flash("Sorry, answer board you want to create existed!",'error')
            print("Answer board created existed.") #For debugging purposes 
            return redirect(f"/upload_answer_board/{session.get('current_class_id')}")
         except Exception as e:
            flash("Error occurs while creating answer board. Try again later.",'error')
            print("Internal server error.",e) #For debugging purposes 
            return redirect(f"/upload_answer_board/{session.get('current_class_id')}")

   return render_template("upload_answer_board.html", classCode=session.get('current_class_id'), answerBoardId=session.get('current_answer_board_id'))

@app.route('/get_pdf/<path:filepath>')
def get_pdf(filepath):
    print('Final file path:',filepath)
    directory = os.path.dirname(filepath)  
    file = os.path.basename(filepath)
    print(f"Directory: {directory}, file: {file}")
    return send_from_directory(directory, file, mimetype='application/pdf')

@app.route('/setup_answer_field/<class_id>/<answer_board_id>', methods=['GET','POST'])
def setup_answer_field(class_id, answer_board_id):
  ans_board = ANSWER_BOARD.query.filter_by(ANSWER_BOARD_ID=answer_board_id).first()
  print(f"Answer board: {ans_board}")
  paper_id = ans_board.PAPER_ID
  print(f"Paper ID: {paper_id}")
  if paper_id:
    paper_info = PASTPAPERS_INFO.query.filter_by(PAPER_ID=paper_id).first()
    print(f"Paper Info: {paper_info}")
    paper_path = paper_info.FILEPATH
    print(f"Paper path: {paper_path}")
  else:
    flash("Unexpected error.",'error')
    print("No paper id found!")
    return redirect(f"/upload_answer_board/{session.get('current_class_id')}")
  
  #When user submit form
  if request.method == 'POST':
    #Get user input from form 
    form_data = request.form
    print(f"Inputs received: {form_data}")
    question_data = []

    for key in form_data:
      if key.startswith('question') and '-' not in key:  # only top-level question fields
        question_id = key.replace('question', '') 
        if not question_id:
           question_id = 1
        question_text = form_data[key]
        answer_type = form_data.get(f'type-ans{question_id}', 'text')
        mcq_type = form_data.get(f'type-mcq{question_id}',None) if answer_type == 'mcq' else None

        question_entry = {
            'question': question_text,
            'type': answer_type,
            'mcq_type': int(mcq_type) if mcq_type else None
        }

        print(f"Question {question_id} record: {question_entry}")
        question_data.append(question_entry)
    
    try:
      #Handle data from user and save into database 
      for question in question_data:
        question_desc = question['question']
        question_type = question['type']
        

        if question_type == "text":
            question_type_no = 1
        elif question_type == "mcq":
            question_type_no = 2
        elif question_type == "file":
            question_type_no = 3

        ans_field_id = uuid.uuid4().hex[:10]
        new_record1 = ANSWER_FIELD(ANSWER_FIELD_ID=ans_field_id, ANSWER_FIELD_DESC=question_desc, ANSWER_FIELD_TYPE=question_type_no, ANSWER_BOARD_ID=answer_board_id, MCQ_TYPE=question['mcq_type'])
        print(f"Record will insert into ANSWER_FIELD: {new_record1}")
        db.session.add(new_record1)
      db.session.commit()
      flash("Answer field setup successfully!",'success')
      return render_template("setup_answer_field.html",paperPath=paper_path,classCode=session.get('current_class_id'))
    except Exception as e:
      flash("Error occurs while setup answer field. Please try again.",'error')
      print("Error occurs while setup answer field.",e)
      return redirect(f'/setup_answer_field/{session.get("current_class_id")}/{answer_board_id}')
    
  return render_template("setup_answer_field.html",paperPath=paper_path, classCode=session.get('current_class_id'))

@app.route('/open_answer_board/<class_id>/<answer_board_id>', methods=['GET', 'POST'])
def open_answer_board(class_id, answer_board_id):
    session['current_answer_board_id'] = answer_board_id
    ans_board = ANSWER_BOARD.query.filter_by(ANSWER_BOARD_ID=answer_board_id).first()

    user_id = session.get('user_id')
    user_info = USER_INFO.query.filter_by(USER_ID=user_id).first()
    name = user_info.NAME

    if ans_board:
      paper = PASTPAPERS_INFO.query.filter_by(PAPER_ID=ans_board.PAPER_ID).first()
      paper_path = paper.FILEPATH if paper else None  # Get the filepath
    else:
      flash("Answer board not found.", "error")
      return redirect(url_for('view_class'))

    paper = PASTPAPERS_INFO.query.filter_by(PAPER_ID=ans_board.PAPER_ID).first()
    paper_path = paper.FILEPATH if paper else None
    answer_board_name = ans_board.ANSWER_BOARD_NAME

    answer_fields = ANSWER_FIELD.query.filter_by(ANSWER_BOARD_ID=answer_board_id).all()

    return render_template(
        "view_answer_board.html", 
        paperPath=paper_path, 
        answer_board_name=answer_board_name,
        answer_fields=answer_fields,
        class_id=class_id,               # <-- add this
        answer_board_id=answer_board_id,  # <-- add this
        username=name
    )

@app.route('/class_info/<class_id>', methods=['POST','GET'])
def class_info(class_id):
  class_info = CLASS.query.filter_by(CLASS_ID=session.get('current_class_id')).first()
  print(f"Class info: {class_info}")
  subject_info = SUBJECT_INFO.query.filter_by(SUBJECT_ID = class_info.SUBJECT_ID).first()
  subjectName = f"{class_info.SUBJECT_ID} - {subject_info.SUBJECT_DESC}"
  term_info = TERM_INFO.query.filter_by(TERM_ID=class_info.TERM_ID).first()
  termName = f"{class_info.TERM_ID} - {term_info.TERM_DESC}"

  class_record = {
     'classCode': class_id,
     'className': class_info.CLASS_NAME,
     'subject': subjectName,
     'term': termName
  }

  #When edit button is submitted
  if request.method == 'POST':
    newClassName = request.form.get('class_name')

    if not newClassName:
       flash("Please enter a new class name!",'error')
       print("Class name empty. ")
       return redirect(f'/class_info/{session.get("current_class_id")}')
    
    record = CLASS.query.filter_by(CLASS_ID=session.get('current_class_id')).first()

    try:
       if record:
          record.CLASS_NAME = newClassName
          record.LAST_MODIFIED_BY = session.get('user_id')
          record.LAST_MODIFIED_ON = datetime.now()
          db.session.commit()
          flash("Successfully edited class info!",'success')
          print("Success edit class info.")
          return render_template("class_info.html", class_record=class_record, classCode = session.get('current_class_id'))
    except Exception as e:
       flash("Error occurs while editing class info. Please try again later.",'error')
       print("Internal server error.", e)
       return redirect(f'/class_info/{session.get("current_class_id")}')

  return render_template("class_info.html", class_record=class_record, classCode = session.get('current_class_id'))

@app.route('/join_class_link/<class_id>', methods=['GET','POST'])
def join_class_link(class_id):
  session_user = session.get('user_id')
  if not session_user:
     flash("Please login before join a class!",'error')
     print("Not logged in yet.")
     session['pending_class'] = class_id
     return redirect(url_for('login'))

  already_joined = USER_CLASS.query.filter_by(CLASS_ID=class_id, USER_ID=session_user).first()
  print("User already joined:",already_joined) #For debugging purposes
  if already_joined:
      flash('You joined this class!','error')
      print("User joined this class!") #For debugging purposes 

      records = USER_CLASS.query.filter_by(USER_ID=session.get('user_id')).all()
      print("User class:", records)
      classIds = [record.CLASS_ID for record in records]
      print(f"Class ID under user {session.get('user_id')} : {classIds}")

      classes = CLASS.query.filter(CLASS.CLASS_ID.in_(classIds)).all()

      class_records = []
      for cls in classes:
        lecturer = USER_INFO.query.filter_by(USER_ID=cls.CREATED_BY).first()
        class_records.append({
            'classID': cls.CLASS_ID,
            'className': cls.CLASS_NAME,
            'termID': cls.TERM_ID,
            'lecturerName': lecturer.NAME if lecturer else 'Unknown'
        })

      print("Final record:", class_records)
      return render_template("view_class.html",records=class_records)
  else:
      new_record = USER_CLASS(USER_ID=session_user, CLASS_ID=class_id, JOINED_AT=datetime.now())
      db.session.add(new_record)
      db.session.commit()
      flash('Join class successfully!','success')
      print("Join class action success.") #For debugging purposes 
      return redirect(url_for('open_class', class_id=class_id, showAlert=False))
      
@app.route('/view_subjects')
def view_subjects():
    # Query with explicit joins
    subjects = db.session.query(
        SUBJECT_INFO,
        STUDY_LVL_INFO.STUDY_LVL_DESC,
        FACULTY_INFO.FACULTY_DESC
    ).join(
        STUDY_LVL_INFO, 
        SUBJECT_INFO.STUDY_LVL_ID == STUDY_LVL_INFO.STUDY_LVL_ID
    ).join(
        FACULTY_INFO,
        SUBJECT_INFO.FACULTY_ID == FACULTY_INFO.FACULTY_ID
    ).all()
    
    return render_template('view_subjects.html', subjects=subjects, class_id='none')

@app.route('/edit_subject/<subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    subject = SUBJECT_INFO.query.get_or_404(subject_id)
    study_levels = STUDY_LVL_INFO.query.all()
    faculties = FACULTY_INFO.query.all()

    if request.method == 'POST':
        try:
            # Update subject information
            subject.SUBJECT_ID = request.form['subject_id']
            subject.SUBJECT_DESC = request.form['subject_desc']
            subject.STUDY_LVL_ID = request.form['study_lvl']
            subject.FACULTY_ID = request.form['faculty']
            
            db.session.commit()
            flash('Subject updated successfully!', 'success')
            print("Subject updates successfully!")
            return render_template("edit_subject.html", subject=subject,
                         study_levels=study_levels,
                         faculties=faculties)
        except IntegrityError:
            db.session.rollback()
            flash('Subject ID already exists!', 'error')
            print("Subject ID exists!")
            return redirect(url_for('edit_subject'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating subject: {str(e)}', 'error')
            print("Internal server error",e)
            return redirect(url_for('edit_subject'))

    return render_template('edit_subject.html', 
                         subject=subject,
                         study_levels=study_levels,
                         faculties=faculties)

@app.route('/delete_subject/<subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = SUBJECT_INFO.query.get_or_404(subject_id)
    try:
        db.session.delete(subject)
        db.session.commit()
        flash('Subject deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting subject: {str(e)}', 'error')
    return redirect(url_for('view_subjects'))

@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    study_levels = STUDY_LVL_INFO.query.all()
    faculties = FACULTY_INFO.query.all()

    if request.method == 'POST':
        try:
            # Validate required fields
            if not all([request.form['subject_id'], 
                       request.form['subject_desc'],
                       request.form['study_lvl'],
                       request.form['faculty']]):
                flash('All fields are required!', 'error')
                return redirect(url_for('add_subject'))

            # Check for existing subject ID
            if SUBJECT_INFO.query.get(request.form['subject_id']):
                flash('Subject ID already exists!', 'error')
                return redirect(url_for('add_subject'))

            new_subject = SUBJECT_INFO(
                SUBJECT_ID=request.form['subject_id'],
                SUBJECT_DESC=request.form['subject_desc'],
                STUDY_LVL_ID=request.form['study_lvl'],
                FACULTY_ID=request.form['faculty']
            )

            db.session.add(new_subject)
            db.session.commit()
            flash('Subject added successfully!', 'success')
            return redirect(url_for('view_subjects'))

        except IntegrityError as e:
            db.session.rollback()
            flash('Invalid study level or faculty selected!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding subject: {str(e)}', 'error')

    return render_template('add_subject.html',
                         study_levels=study_levels,
                         faculties=faculties)

@app.route('/edit_answer_board/<class_id>/<answer_board_id>', methods=['GET','POST'])
def edit_answer_board(class_id, answer_board_id):
  ans_board = ANSWER_BOARD.query.filter_by(ANSWER_BOARD_ID=answer_board_id).first()
  print(f"Answer board: {ans_board}")
  paper_id = ans_board.PAPER_ID
  print(f"Paper ID: {paper_id}")
  if paper_id:
    paper_info = PASTPAPERS_INFO.query.filter_by(PAPER_ID=paper_id).first()
    print(f"Paper Info: {paper_info}")
    paper_path = paper_info.FILEPATH
    print(f"Paper path: {paper_path}")
  else:
    flash("Unexpected error.",'error')
    print("No paper id found!")
    return redirect(f"/upload_answer_board/{session.get('current_class_id')}")

  ans_fields = ANSWER_FIELD.query.filter_by(ANSWER_BOARD_ID=answer_board_id).all()
  print(f"Ans field from db: {ans_fields}")

  ans_field_datas = []

  for ans_field in ans_fields:
    ans_field_dict = {
       'question_id': ans_field.ANSWER_FIELD_ID,
       'question_name': ans_field.ANSWER_FIELD_DESC,
       'question_type': ans_field.ANSWER_FIELD_TYPE,
       'mcq_type': ans_field.MCQ_TYPE
    }

    ans_field_datas.append(ans_field_dict)

  print(f"Final answer field record: {ans_field_datas}.")

  if request.method == 'POST':
    #Get user input from form 
    form_data = request.form
    print(f"Inputs received: {form_data}")
    question_data = []
    try:
      for key in form_data:
        if key.startswith('question') and '-' not in key:  # only top-level question fields
          question_id = key.replace('question', '') 
          if not question_id:
            question_id = 1
          ques_id = form_data.get(f'ques_id{question_id}', '')
          question_text = form_data[key]
          answer_type = form_data.get(f'type-ans{question_id}', 'text')
          mcq_type = form_data.get(f'type-mcq{question_id}',None) if answer_type == 'mcq' else None
          deleted_ids_str = request.form.get('deleted_questions', '')
          deleted_ids = [id.strip() for id in deleted_ids_str.split(',') if id.strip()]

          for del_id in deleted_ids: 
            field_to_delete = ANSWER_FIELD.query.filter_by(ANSWER_FIELD_ID=del_id).first()
            print(f"Field to be deleted:{field_to_delete}")
            if field_to_delete:
              db.session.delete(field_to_delete)

          if answer_type == 'text':
            answer_type_no = 1
            mcq_type = None
          elif answer_type == 'mcq':
            answer_type_no = 2
          elif answer_type == 'file':
            answer_type_no = 3
            mcq_type = None
          else:
            answer_type_no = 1
            mcq_type = None
          
          question_entry = {
            'ques_id': ques_id,
            'question': question_text,
            'type': answer_type_no,
            'mcq_type': int(mcq_type) if mcq_type else None
          }

          print(f"Question {question_id} record: {question_entry}")
          question_data.append(question_entry)

          if ques_id:
            answer_field = ANSWER_FIELD.query.filter_by(ANSWER_FIELD_ID=ques_id).first()
            answer_field.ANSWER_FIELD_DESC = question_text
            answer_field.ANSWER_FIELD_TYPE = answer_type_no
            answer_field.MCQ_TYPE = int(mcq_type) if mcq_type else None 
          else:
            new_record = ANSWER_FIELD(ANSWER_FIELD_ID=uuid.uuid4().hex[:10], ANSWER_FIELD_DESC=question_text, ANSWER_FIELD_TYPE=answer_type_no, ANSWER_BOARD_ID=session.get('current_answer_board_id'), MCQ_TYPE=mcq_type)
            print(f"Record going to be inserted: {new_record}")
            db.session.add(new_record)
      db.session.commit()
      flash("Edit answer field successfully!",'success')
      print("Successfully edit answer field!")
      return render_template("edit_answer_board.html", paperPath=paper_path, ans_field_datas=ans_field_datas)
    except Exception as e:
      db.session.rollback()
      flash("Error occurs while editing answer field. Try again later.",'error')
      print("Internal server error",e)
      return redirect(url_for('edit_answer_board', class_id=session.get('current_class_id'), answer_board_id=session.get('current_answer_board_id')))
    
  return render_template("edit_answer_board.html", paperPath=paper_path, ans_field_datas=ans_field_datas)

@app.route('/submit_answers/<class_id>/<answer_board_id>', methods=['POST'])
def submit_answers(class_id, answer_board_id):
    
    student_id = session.get('user_id')  
    submitted_data = request.form
    uploaded_files = request.files

    # Retrieve related answer fields
    answer_fields = ANSWER_FIELD.query.filter_by(ANSWER_BOARD_ID=answer_board_id).all()

    try:
        for index, field in enumerate(answer_fields, start=1):
            answer_id = uuid.uuid4().hex[:10]
            answer_field_id = field.ANSWER_FIELD_ID
            answer_by = student_id
            answer_on = datetime.now()

            form_key = f'answer{index}'
            answer_type = field.ANSWER_FIELD_TYPE

            if answer_type == 3:  # File upload
                file = uploaded_files.get(form_key)
                if file:
                    filename = f"{uuid.uuid4().hex}_{file.filename}"
                    file_path = os.path.join('static', 'student_uploads', filename)
                    file.save(file_path)
                    answer_content = file_path
                else:
                    answer_content = None
            else:
                answer_content = submitted_data.get(form_key)

            new_answer = ANSWER(
                ANSWER_ID=answer_id,
                ANSWER_FIELD_ID=answer_field_id,
                ANSWER_BY=answer_by,
                ANSWER_ON=answer_on,
                ANSWER_CONTENT=answer_content
            )
            db.session.add(new_answer)

        db.session.commit()
        print("Answer submitted successfully!",new_answer)
        flash("Answers submitted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print("Error saving answers:", e)
        flash("Failed to submit answers. Please try again.", "error")

    return redirect(url_for('open_answer_board', class_id=class_id, answer_board_id=answer_board_id))

@app.route('/terms')
def view_terms():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    pagination = TERM_INFO.query.order_by(TERM_INFO.TERM_ID).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    return render_template('view_terms.html', terms=pagination.items, pagination=pagination)

@app.route('/add_term', methods=['GET', 'POST'])
def add_term():
    if request.method == 'POST':
        try:
            term_id = request.form['term_id']
            term_desc = request.form['term_desc']
            if not term_desc or not term_id:
                flash('All fields are required!', 'error')
                return redirect(url_for('add_term'))

            new_term = TERM_INFO(TERM_ID=term_id, TERM_DESC=term_desc)
            db.session.add(new_term)
            db.session.commit()
            flash('Term added successfully!', 'success')
            return redirect(url_for('view_terms'))

        except IntegrityError:
            db.session.rollback()
            flash('Term already exists!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding term: {str(e)}', 'error')

    return render_template('add_term.html')

@app.route('/edit_term/<term_id>', methods=['GET', 'POST'])
def edit_term(term_id):
    term = TERM_INFO.query.get_or_404(term_id)
    if request.method == 'POST':
        try:
            term.TERM_DESC = request.form['term_desc']
            db.session.commit()
            flash('Term updated successfully!', 'success')
            return redirect(url_for('view_terms'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating term: {str(e)}', 'error') 
            return redirect(url_for('edit_term', term_id=term_id))
    return render_template('edit_term.html', term=term)


@app.route('/delete_term/<term_id>', methods=['POST'])
def delete_term(term_id):
    term = TERM_INFO.query.get_or_404(term_id)
    try:
        db.session.delete(term)
        db.session.commit()
        flash('Term deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()

@app.route("/chat_history/<answer_board_id>")
def chat_history(answer_board_id):
   try:
        messages = CHAT_MESSAGE.query.filter_by(ANSWER_BOARD_ID=answer_board_id).order_by(CHAT_MESSAGE.TIMESTAMP).all()
        
        messages_info = []
        for message in messages:
            user_info = USER_INFO.query.filter_by(USER_ID=message.SENT_BY).first()
            username = user_info.NAME if user_info else "Unknown"
            
            msg_dict = {
                "sender": username,
                "message": message.MESSAGE_CONTENT,
                "image_url": message.IMAGE_URL,
                "timestamp": message.TIMESTAMP.strftime("%Y-%m-%d %H:%M") if message.TIMESTAMP else ""
            }
            messages_info.append(msg_dict)

        print(messages_info)
        return jsonify(messages=messages_info)

   except Exception as e:
        # Log the full error for debugging
        import traceback
        print("ERROR in chat_history():", traceback.format_exc())
        return jsonify({"error": "Something went wrong."}), 500

@app.route('/send-message', methods=['POST'])
def send_message():
   sender_info = session.get('user_id','Anonymous')
   if sender_info != "Anonymous":
      senders = USER_INFO.query.filter_by(USER_ID=sender_info).first()
      sender_name = senders.NAME
   else:
      sender_name = "Anonymous"
    
   text = request.form.get('chat-text').strip()
   answer_board_id = session.get('current_answer_board_id')
   file = request.files.get('chat-image')
   
   print(f"Sender: {sender_info}, Message content: {text}, Current Ans Board: {answer_board_id}, File received: {file}")

   image_url = None
   if file and file.filename:
      ext = file.filename.rsplit('.', 1)[1].lower()
      if ext in {'jpg','png','jpeg','gif'}:
         filename = secure_filename(file.filename)
         filepath = os.path.join('static/chat',filename)
         file.save(filepath)
         image_url = f"/{filepath}"
   
   new_msg = CHAT_MESSAGE(CHAT_ID=uuid.uuid4().hex[:20], ANSWER_BOARD_ID=answer_board_id, SENT_BY=sender_info, MESSAGE_CONTENT=text if text else None, IMAGE_URL=image_url)
   db.session.add(new_msg)
   db.session.commit()
   
   print(f"Emitting message to room: answerboard_{answer_board_id}")
   socketio.emit("message", {
      "sender": sender_name,
      "msg": text,
      "image_url": image_url
   }, room=f"answerboard_{answer_board_id}")

   return jsonify(success=True)

if __name__ == "__main__":
    #app.run(debug=True)
    socketio.run(app, debug=True)