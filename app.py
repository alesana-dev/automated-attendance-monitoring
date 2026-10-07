from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail, Message
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Database Config ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smarttrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Flask-Mail Config ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'masarappancitcanton@gmail.com'     
app.config['MAIL_PASSWORD'] = 'opwyjigutdxrxgpz'         
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

# --- Extension Instances ---
from models import db  # Import the UNBOUND db instance
db.init_app(app)       # Bind db to app here!

migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'routes.login'
mail = Mail(app)

# --- Import models after app and db are set up ---
from models import User, Student, Attendance

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Register your routes blueprint ---
from routes import app_routes
app.register_blueprint(app_routes)

if __name__ == '__main__':
    print("Starting SmartTrack Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
