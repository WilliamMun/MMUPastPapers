from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mmupastpapers.db'
db = SQLAlchemy(app)

###Database is not setted yet. Temporarily commit for exercise purpose. 
class todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.timezone.utc)

    def __repr__(self):
        return '<Task %r>' % self.id

@app.route('/')
def main():
    return render_template("main.html")

if __name__ == "__main__":
    app.run(debug=True)
