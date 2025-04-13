from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
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

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Add authentication logic here
        return redirect('/')
    return render_template("login.html")

@app.route('/')
def main():
    return render_template("main.html")

if __name__ == "__main__":
    app.run(debug=True)