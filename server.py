from flask import Flask, render_template, request, redirect, flash, url_for, session
from sqlite3 import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = "MmUPastPap3rs2510@CSP1123"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///mmupastpapers.db"
db = SQLAlchemy(app)

#-----------------------------------------------------------------------------------------------------------
#Create database tables  
#ENTITY: USER_INFO 
class USER_INFO(db.Model):  
  USER_ID = db.Column(db.String(50), primary_key=True) 
  USERNAME = db.Column(db.String(200), nullable=False) 
  PASSWORD = db.Column(db.String(255), nullable=False) 
  ROLES = db.Column(db.Integer, nullable=False) #1 indicates student; 2 indicates lecturer  
  CREATED_ON = db.Column(db.DateTime, default=datetime.utcnow) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.utcnow, nullable=True) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 
 
#ENTITY: SECURITY_QUES 
class SECURITY_QUES(db.Model): 
  SECURITY_QUES_ID = db.Column(db.String(100), primary_key=True) 
  SECURITY_QUES_DESC = db.Column(db.Text, nullable=False) 
 
#ENTITY: SECURITY_QUES_ANS 
class SECURITY_QUES_ANS(db.Model): 
  USER_ID = db.Column(db.String(50), db.ForeignKey(USER_INFO.USER_ID)) 
  SECURITY_QUES_ID = db.Column(db.String(100), db.ForeignKey(SECURITY_QUES.SECURITY_QUES_ID)) 
  ANSWER = db.Column(db.Text) 
  CREATED_ON = db.Column(db.DateTime, default=datetime.utcnow, nullable=True) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.utcnow, nullable=True) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 

  __table_args__ = (db.PrimaryKeyConstraint('USER_ID','SECURITY_QUES_ID'),)

#ENTITY: STUDY_LVL_INFO  
class STUDY_LVL_INFO(db.Model): 
  STUDY_LVL_ID = db.Column(db.String(4), primary_key=True) 
  STUDY_LVL_DESC = db.Column(db.Text, nullable=False) 

#ENTITY: FACULTY_INFO  
class FACULTY_INFO(db.Model): 
  FACULTY_ID = db.Column(db.String(3), primary_key=True) 
  FACULTY_DESC = db.Column(db.Text, nullable=False) 

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
  UPLOAD_ON = db.Column(db.DateTime, default=datetime.utcnow) 
  UPLOAD_BY = db.Column(db.String(50)) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.utcnow) 
 
#ENTITY: CLASS 
class CLASS(db.Model): 
  CLASS_ID = db.Column(db.String(50), primary_key=True) 
  CLASS_NAME = db.Column(db.Text, nullable=False) 
  CREATED_BY = db.Column(db.String(50), nullable=False) 
  CREATED_ON = db.Column(db.DateTime, default=datetime.utcnow) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.utcnow) 
  SUBJECT_ID = db.Column(db.String(7), db.ForeignKey(SUBJECT_INFO.SUBJECT_ID)) 
  STUDY_LVL_ID = db.Column(db.String(4), db.ForeignKey(STUDY_LVL_INFO.STUDY_LVL_ID)) 
  FACULTY_ID = db.Column(db.String(3), db.ForeignKey(FACULTY_INFO.FACULTY_ID)) 
  TERM_ID = db.Column(db.Integer, db.ForeignKey(TERM_INFO.TERM_ID))  
 
#ENTITY: USER_CLASS 
class USER_CLASS(db.Model): 
  USER_ID = db.Column(db.String(50), db.ForeignKey(USER_INFO.USER_ID)) 
  CLASS_ID = db.Column(db.String(50), db.ForeignKey(CLASS.CLASS_ID)) 
  JOINED_AT = db.Column(db.DateTime, default=datetime.utcnow) 

  __table_args__ = (db.PrimaryKeyConstraint('USER_ID','CLASS_ID'),)
 
#ENTITY: ANSWER_FIELD 
class ANSWER_FIELD(db.Model): 
  ANSWER_FIELD_ID = db.Column(db.String(50), primary_key=True) 
  PAPER_ID = db.Column(db.String(50), db.ForeignKey(PASTPAPERS_INFO.PAPER_ID)) 
  ANSWER_FIELD_DESC = db.Column(db.Text, nullable=True) 
  ANSWER_FIELD_TYPE = db.Column(db.Integer, nullable=False) #1: Text field, 2: MCQ, 3: Upload image 
 
#ENTITY: ANSWER  
class ANSWER(db.Model): 
  ANSWER_ID = db.Column(db.String(50), primary_key=True)
  ANSWER_FIELD_ID = db.Column(db.String(50), db.ForeignKey(ANSWER_FIELD.ANSWER_FIELD_ID)) 
  ANSWER_BY = db.Column(db.String(50), nullable=False) 
  ANSWER_ON = db.Column(db.DateTime, default=datetime.utcnow) 
  ANSWER_CONTENT = db.Column(db.Text) 
 
#ENTITY: DISCUSSION_SPACE 
class DISCUSSION_SPACE(db.Model): 
  DISCUSSION_ID = db.Column(db.String(50), primary_key=True) 
  PAPER_ID = db.Column(db.String(50), db.ForeignKey(PASTPAPERS_INFO.PAPER_ID)) 
  CLASS_ID = db.Column(db.String(50), db.ForeignKey(CLASS.CLASS_ID)) 
  CREATED_BY = db.Column(db.String(50), nullable=False) 
  CREATED_ON = db.Column(db.DateTime, default=datetime.utcnow) 
 
#ENTITY: DISCUSSION_FORUM 
class DISCUSSION_FORUM(db.Model): 
  COMMENT_ID = db.Column(db.String(100), primary_key=True) 
  COMMENT = db.Column(db.Text) 
  DISCUSSION_ID = db.Column(db.String(50), db.ForeignKey(DISCUSSION_SPACE.DISCUSSION_ID)) 
  POSTED_BY = db.Column(db.String(50), nullable=False) 
  POSTED_ON = db.Column(db.DateTime, default=datetime.utcnow)

#-------------------------------------------------------------------------------------------------------
#Finish setting up database tables 

def isStrongPassword(password):
  pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{10,}$'
  return bool(re.match(pattern, password))

@app.route('/login',methods=['GET','POST'])
def login():
    status = True #Flag to determine whether user input is valid or invalid 

    if request.method == 'POST':
        #Retrive user input 
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        print(username, password) #For debugging purposes 

        #Input verification 
        if not username or not password:
            flash('Username and password are required', 'error')
            status = False
            print("Username or password is empty.") #For debugging purposes
            return redirect('/login')

        
        #Retrive data from database 
        user = USER_INFO.query.filter_by(USER_ID=username).first()
        print(user) #For debugging purposes
        if not user:
            flash('Invalid username.', 'error')
            status = False
            print(f"Invalid username {username}") #For debugging purposes
            print(user == username) #For debugging purposes
            return redirect('/login')
        if not check_password_hash(user.PASSWORD, password):
            flash('Invalid password', 'error')
            status = False
            print(f"Invalid password {password}") #For debugging purposes
            print(password == user.PASSWORD) #For debugging purposes
            print(check_password_hash(user.PASSWORD, password)) #For debugging purposes
            return redirect('/login')
        
        if status == True:
          session['user_id'] = user.USER_ID
          session['username'] = user.USERNAME
          session['roles'] = user.ROLES
          flash('Login successful!', 'success')
          print(f"Login successful for user {username}.") #For debugging purposes
          return render_template('login.html')
        
    return render_template("login.html")

@app.route('/register' ,methods=['GET','POST'])
def register():
    
    if request.method == 'POST':
        #Retrive user input 
        username = request.form['username'].strip()
        userid = request.form.get('userid').strip().lower()
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

        print(f"New registration info: {username},{userid},{password},{roles},{rolesNum}.") #For debugging purposes 

        #Input verification 
        if password != confirm_password:
           flash('Passwords do not match.', 'error')
           print(f"Passwords do not match. New password:{password} vs Confirm password:{confirm_password}.") #For debugging purposes 
           return redirect('/register')
        
        if not all ([username, userid, password, confirm_password, roles]):
           flash('All fields are required.', 'error')
           print("All/some fields are empty.") #For debugging purposes
           return redirect('/register')
        
        if not isStrongPassword(password):
           flash("Password must be at least 10 characters, contains at least 1 uppercase, 1 lowercase, 1 symbol and 1 digit.", "error")
           print("Password does not meet the requirements.") #For debugging purposes
           return redirect('/register')
        
        #Retrive data from database 
        user_db = USER_INFO.query.filter_by(USERNAME=username).first()
        user_id_db = USER_INFO.query.filter_by(USER_ID=userid).first()
        print(f"Username: {user_db}, User ID: {user_id_db}") #For debugging purposes

        #Avoid duplication of data 
        if user_db:
           flash('Username already existed.', 'error')
           return redirect('/register')
        if user_id_db:
           flash('Email already existed.', 'error')
           return redirect('/register')
        if rolesNum == None:
           flash('Invalid option for User Type.', 'error')
           print(f"Invalid roles: {rolesNum}") #For debugging purposes
           print(f"Roles selected: {roles}") #For debugging purposes
           return redirect('/register')

        try:
           new_user = USER_INFO(USER_ID=userid, USERNAME=username, PASSWORD=generate_password_hash(password), ROLES=rolesNum)
           db.session.add(new_user)
           db.session.commit()
           flash('User registered successfully!', 'success')
           print(f"User {userid} succesfully registered")
           return render_template("register.html")
        except IntegrityError:
           db.session.rollback()
           flash('Username or email already exists.', 'error')
           print("Username or email already exists.")
           return redirect('/register')
        except Exception as e:
           db.session.rollback()
           flash('Error occurred while registering user. Please try again later', 'error')
           print("Internal server error.")
           return redirect('/register')
    return render_template("register.html")

@app.route('/')
def main():
    return render_template("main.html")

@app.route('/resetPassword', methods=['GET', 'POST'])
def resetPassword():
  questions = SECURITY_QUES.query.all()

  if request.method == 'POST':

    #Retrive user input
    userID = request.form['userID']
    new_password = request.form['newPassword']
    confirm_password = request.form['confirmPassword']
    question_id = request.form['securityQuestion']
    answer = request.form['securityAnswer']

    #User input verification
    if not userID or not new_password or not confirm_password or not question_id or not answer:
      flash("Please fill in all information!", "error")
      print("Please fill in all information!") #For debugging purposes
      return redirect(url_for('resetPassword'))
    
    if not isStrongPassword(new_password):
      flash("Password must be at least 10 characters, contains at least 1 uppercase, 1 lowercase, 1 symbol and 1 digit.", "error")
      print("Password does not match requirements.") #For debugging purposes
      return redirect(url_for('resetPassword'))

    if new_password != confirm_password:
      flash("Passwords do not match!", "error")
      print("Passwords do not match!") #For debugging purposes
      return redirect(url_for('resetPassword'))

    #Save new data into database
    try:
      user = USER_INFO.query.filter_by(USER_ID=userID).first()
      print(user)

      if user:
        record = SECURITY_QUES_ANS.query.filter_by(USER_ID=userID, SECURITY_QUES_ID=question_id, ANSWER=answer).first()
        print(record) #For debugging purposes

        if record:
          user = USER_INFO.query.filter_by(USER_ID=userID).first()
          user.PASSWORD = generate_password_hash(new_password)
          db.session.commit()
          flash("Password reset successfully!", "success")
          print(f"Password reset sucessfully for user {userID}, {question_id}, the new password is {new_password}.") #For debugging purposes
          return render_template("resetPassword.html")
        
        elif record == None:
          flash("Incorrect answer for security question. Try again.", "error")
          print(f"Incorrect answer for security question.") #For debugging purposes 
          return redirect(url_for('resetPassword'))
      
      else:
         flash("Username does not exist.", "error")
         print(f"Username {userID} does not exists") #For debugging purposes 
         return redirect(url_for('resetPassword'))
    
    except Exception as e:
      db.session.rollback()
      flash("Error occurred while registering user. Please try again later", "error")
      print("Internal server error.")
      return redirect(url_for('resetPassword'))
    
  return render_template('resetPassword.html', questions=questions)

if __name__ == "__main__":
    app.run(debug=True)