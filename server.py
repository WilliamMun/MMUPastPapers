from flask import Flask, render_template, request, redirect, flash, url_for, session, make_response
from flask import send_file, abort
import os
from sqlite3 import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import re
import uuid

app = Flask(__name__)
app.secret_key = "MmUPastPap3rs2510@CSP1123"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///mmupastpapers.db"
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['ALLOWED_EXTENSION'] = {'pdf', 'docx'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16MB
db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) #Create upload folder if it doesn't exist

#-----------------------------------------------------------------------------------------------------------
#Create database tables  
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
  UPLOAD_ON = db.Column(db.DateTime, default=datetime.now) 
  UPLOAD_BY = db.Column(db.String(50)) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.now) 
 
#ENTITY: CLASS 
class CLASS(db.Model): 
  CLASS_ID = db.Column(db.String(50), primary_key=True) 
  CLASS_NAME = db.Column(db.Text, nullable=False) 
  CREATED_BY = db.Column(db.String(50), nullable=False) 
  CREATED_ON = db.Column(db.DateTime, default=datetime.now) 
  LAST_MODIFIED_BY = db.Column(db.String(50), nullable=True) 
  LAST_MODIFIED_ON = db.Column(db.DateTime, default=datetime.now) 
  SUBJECT_ID = db.Column(db.String(7), db.ForeignKey(SUBJECT_INFO.SUBJECT_ID)) 
  STUDY_LVL_ID = db.Column(db.String(4), db.ForeignKey(STUDY_LVL_INFO.STUDY_LVL_ID)) 
  FACULTY_ID = db.Column(db.String(3), db.ForeignKey(FACULTY_INFO.FACULTY_ID)) 
  TERM_ID = db.Column(db.Integer, db.ForeignKey(TERM_INFO.TERM_ID))  
 
#ENTITY: USER_CLASS 
class USER_CLASS(db.Model): 
  USER_ID = db.Column(db.String(50), db.ForeignKey(USER_INFO.USER_ID)) 
  CLASS_ID = db.Column(db.String(50), db.ForeignKey(CLASS.CLASS_ID)) 
  JOINED_AT = db.Column(db.DateTime, default=datetime.now) 

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
  ANSWER_ON = db.Column(db.DateTime, default=datetime.now) 
  ANSWER_CONTENT = db.Column(db.Text) 
 
#ENTITY: DISCUSSION_SPACE 
class DISCUSSION_SPACE(db.Model): 
  DISCUSSION_ID = db.Column(db.String(50), primary_key=True) 
  PAPER_ID = db.Column(db.String(50), db.ForeignKey(PASTPAPERS_INFO.PAPER_ID)) 
  CLASS_ID = db.Column(db.String(50), db.ForeignKey(CLASS.CLASS_ID)) 
  CREATED_BY = db.Column(db.String(50), nullable=False) 
  CREATED_ON = db.Column(db.DateTime, default=datetime.now) 
 
#ENTITY: DISCUSSION_FORUM 
class DISCUSSION_FORUM(db.Model): 
  COMMENT_ID = db.Column(db.String(100), primary_key=True) 
  COMMENT = db.Column(db.Text) 
  DISCUSSION_ID = db.Column(db.String(50), db.ForeignKey(DISCUSSION_SPACE.DISCUSSION_ID)) 
  POSTED_BY = db.Column(db.String(50), nullable=False) 
  POSTED_ON = db.Column(db.DateTime, default=datetime.now)

#-------------------------------------------------------------------------------------------------------
#Finish setting up database tables 

def isStrongPassword(password):
  pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{10,}$'
  return bool(re.match(pattern, password))

def allowed_file(filename):
   return '.' in filename and \
          filename.rsplit('.', 1). lower() in app.config['ALLOWED_EXTENSION']

@app.route('/login',methods=['GET','POST'])
def login():
    status = True #Flag to determine whether user input is valid or invalid 

    if request.method == 'POST':
        #Retrive user input 
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
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
          session['email'] = user.USER_EMAIL
          session['name'] = user.NAME
          session['roles'] = user.ROLES
          flash('Login successful!', 'success')
          print(f"Login successful for user {email}.") #For debugging purposes
          return render_template('login.html')
        
    return render_template("login.html")

@app.route('/register' ,methods=['GET','POST'])
def register():
    
    if request.method == 'POST':
        #Retrive user input 
        email = request.form['email'].strip()
        name = request.form['name']
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
           new_user = USER_INFO(USER_ID=userId, USER_EMAIL=email, NAME=name, PASSWORD=generate_password_hash(password), ROLES=rolesNum)
           db.session.add(new_user)
           db.session.commit()
           flash('User registered successfully!', 'success')
           print(f"User {email} succesfully registered")
           return render_template("register.html")
        except IntegrityError:
           db.session.rollback()
           flash('Email already exists.', 'error')
           print("Email already exists.")
           return redirect('/register')
        except Exception as e:
           db.session.rollback()
           flash('Error occurred while registering user. Please try again later', 'error')
           print("Internal server error.")
           return redirect('/register')
    return render_template("register.html")

@app.route('/')
@app.route('/main')
def main():
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
        'initials': initials
      }
    
    else:
       return { }

@app.route('/editProfile', methods=['GET', 'POST'])
def editProfile():
  if request.method == 'POST':
    email = session.get('email')
    name = session.get('name')
    newName = request.form['name']
    newEmail = request.form['email']
    print("New name: ",newName," New email:",newEmail) #For debugging purposes 

    #Input verification / validation 
    if not (newName or newEmail) or newName == '' or newEmail == '':
      flash("All fields are required!",'error')
      print("All/some fields are empty.") #For debugging purposes 
      return redirect('/editProfile') 
    if not re.match(r"^[\w\.-]+@([\w]+\.)*mmu\.edu\.my$", newEmail):
      flash("Please enter a valid MMU email address.", 'error')
      print("Email does not met requirement.") #For debugging purposes 
      return redirect('/editProfile')
    
    #Retrieve data from database and compare 
    emailRecord = USER_INFO.query.filter_by(USER_EMAIL=newEmail).all()
    print("Email record only: ",emailRecord)
    if emailRecord: 
      flash('Email existed! Please enter another email.','error')
      print("Email existed.") #For debugging purposes 
      return redirect('/editProfile')

    #Get user ID 
    emailObject = USER_INFO.query.filter_by(USER_EMAIL=email).first()
    user_ID = emailObject.USER_ID
    print("Email obtain:",email,"and respective user ID:",user_ID) #For debugging purposes

    #Get record 
    record = USER_INFO.query.filter_by(USER_ID=user_ID).first()
    print("Email + name:",record)
    try:
      if record: 
        record.USER_EMAIL = newEmail 
        record.NAME = newName 
        record.LAST_MODIFIED_BY = newEmail 
        record.LAST_MODIFIED_ON = datetime.now()
        db.session.commit()
        session.clear()
        flash('Edit profile successfully! Please login again.','success')
        print("Edit profile success.") #For debugging purposes 
        return render_template('editProfile.html')
      else:
        flash('Email already existed! Please enter another email.','error')
        print("Email existed! 2") #For debugging purposes 
        return redirect('/editProfile')
    except Exception as e:
      flash('Error occurs while editing user profile. Please try again later.','error')
      print("Internal server error.") #For debugging purposes 
      return redirect('/editProfile')
       
  return render_template("editProfile.html")

@app.route('/view_papers')
def view_papers():
    pastpapers_info = PASTPAPERS_INFO.query.all()
    return render_template("view_papers.html", pastpapers_info=pastpapers_info)

@app.route('/view_paper/<paper_id>')
def view_paper(paper_id):
    paper = PASTPAPERS_INFO.query.get(paper_id)
    return send_file(paper.FILEPATH, mimetype='application/pdf')

@app.route('/download_paper/<paper_id>')
def download_paper(paper_id):
    paper = PASTPAPERS_INFO.query.get(paper_id)

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
      session.clear()
      flash("Security questions edited successfully! Please log in again.", 'success')
      print("Sucessfully saved new sec ques.") #For debugging purposes 
      return render_template("securityQues.html")
  return render_template("securityQues.html", user_qa=user_qa)

@app.route('/logout')
def logout():
   session.clear()
   flash('Logged out successfully!', 'success')
   response = make_response(render_template("showAlert.html"))
   response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
   return response

@app.route('/upload_paper', methods=['GET', 'POST'])
def upload_paper():
    if 'roles' not in session or session['roles'] != 2:
        flash('Access denied: Only lecturers can upload papers', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
      file = None
      filepath = None
      try:
         paper_desc = request.form.get('paper_desc').strip()
         term_id = request.form.get('term_id')
         file = request.files.get('file')

         if not all([paper_desc, term_id, file]):
            flash('all fields are required!', 'error')
            return redirect('/upload_paper')
         
         if not allowed_file(file.filename):
            flash('Only PDF and DOCX files are allowed!', 'error')
            return redirect('/upload_paper')
         
         if not TERM_INFO.query.get(term_id):
            flash('Invalid term selected', 'error')
            return redirect('/upload_paper')
        
         orig_filename = secure_filename(file.filename)
         unique_id = uuid.uuid4().hex[:8]
         filename = f"{unique_id}_{orig_filename}"
         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
         file.save(filepath)

         paper_id = uuid.uuid4().hex[:10]
         new_paper = PASTPAPERS_INFO(
            PAPER_ID=paper_id, 
            TERM_ID=term_id, 
            FILENAME=orig_filename, 
            FILEPATH=filepath, 
            PAPER_DESC=paper_desc,
            UPLOAD_BY=session['user'],
            LASY_MODIFIED_BY=session['user']
         )
        
         db.session.add(new_paper)
         db.session.commit()
         flash('Paper uploaded successfully!', 'success')
         return redirect('/view_papers')

      except Exception as e:
        db.session.rollback()
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        flash(f'Error occurred while uploading paper: {str(e)}', 'error')
        app.logger.error(f"upload error: {str(e)}", exc_info=True)

    return render_template('upload_paper.html')

@app.route('/delete_paper/<paper_id>', methods=['POST'])
def delete_paper(paper_id):
    if 'roles' not in session or session['roles'] != 2:
        flash('Access denied: Only lecturers can delete papers', 'error')
        return redirect('/login')
    
    paper = PASTPAPERS_INFO.query.get(paper_id)
    if not paper:
       flash("Paper not found", 'error')
       return redirect('/view_papers')
    
    if paper.UPLOAD_BY != session['email']:
       flash("You can only delete papers you've uploaded", 'error')
       return redirect('/view_papers')
    
    try:
       if os.path.exists(paper.FILEPATH):
          os.remove(paper.FILEPATH)
       db.session.delete(paper)
       db.session.commit()
       flash('Paper deleted successfully!', 'success')
    except Exception as e:
       db.session.rollback()
       flash(f'Error occurred while deleting paper: {str(e)}', 'error')
       app.logger.error(f"delete error: {str(e)}", exc_info=True)

    return redirect('/view_papers')

if __name__ == "__main__":
    app.run(debug=True)