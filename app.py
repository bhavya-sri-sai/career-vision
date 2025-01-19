from flask import Flask, request, jsonify,session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure and random key

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Revathi%40123@localhost:5433/Mydatabase'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing primary key
    username = db.Column(db.String(50), nullable=False)  # Username field
    email = db.Column(db.String(100), unique=True, nullable=False)  # Email field
    password = db.Column(db.String(255), nullable=False)  # Password field
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing primary key
    username = db.Column(db.String(50), nullable=False)  # Username field
    email = db.Column(db.String(100), unique=True, nullable=False)  # Email field
    password = db.Column(db.String(255), nullable=False)  # Password field
    
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    # Define the Question model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.String(500), nullable=True, default='')  # Provide default value for answer column


    def __repr__(self):
        return f'<Question {self.id} - {self.question_text}>'

# Create all tables
with app.app_context():
    db.create_all()
    print("Tables created successfully!")
    
CORS(app)  # Enable CORS for all routes
bcrypt = Bcrypt(app)


# Route for user registration
@app.route('/register', methods=['POST'])
def register():
    
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Check if username or email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"message": "Email already exists!"}), 400

        # Hash the password before saving to the database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create a new user instance
        new_user = User(username=username, email=email, password=hashed_password)

        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        print(f"User {username} registered successfully")  # Log success
        return jsonify({"message": "Registration successful!"}), 201
    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        print(f"Error occurred: {str(e)}")  # Log error message
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500
    return "registeration success"
    #admin
@app.route('/register/admin', methods=['POST'])
def register_admin():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Check if email already exists in the Admin table
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            return jsonify({"message": "Email already exists!"}), 400

        # Hash the password before saving to the database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create a new admin instance
        new_admin = Admin(username=username, email=email, password=hashed_password)

        # Add the admin to the database
        db.session.add(new_admin)
        db.session.commit()

        print(f"Admin {username} registered successfully")  # Log success
        return jsonify({"message": "Admin registration successful!"}), 201
    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        print(f"Error occurred: {str(e)}")  # Log error message
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

# Route for admin login
@app.route('/login/admin', methods=['POST'])
def login_admin():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        # Fetch admin from the Admin table
        admin = Admin.query.filter_by(email=email).first()

        if admin and bcrypt.check_password_hash(admin.password, password):
            session['email'] = admin.email
            return jsonify({"message": "Admin login successful!"}), 200

        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500

@app.route('/view_users', methods=['GET'])
def view_users():
    # Fetch all users from the database
    users = User.query.all()

    # Format the data as a list of dictionaries
    user_data = [
        {"username": user.username, "email": user.email, "password": user.password}
        for user in users
    ]

    return jsonify({"users": user_data})
# Route for user login
@app.route('/login', methods=['GET'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        # Fetch user from the database
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['email'] = user.email
            return jsonify({"message": "Login successful!"}), 200

        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500
@app.route('/courses', methods=['POST'])
def get_courses():
    try:
        courses = Course.query.all()  # Retrieve all courses from the database
        # Format the courses as a list of dictionaries
        courses_list = [{"id": course.id, "name": course.name, "duration": course.duration} for course in courses]
        return jsonify({"courses": courses_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_courses', methods=['GET'])
def filter_courses():
    data = request.get_json()  # Parse the incoming JSON data
    skills = data.get('skills', '').lower()
    qualification = data.get('qualification', '').lower()

    # Validate the input
    if not skills or not qualification:
        return jsonify({"message": "Skills and qualification are required."}), 400

    try:
        # Retrieve all courses
        courses = Course.query.all()

        # Filter courses based on the provided skills and qualification
        matching_courses = [
            {"id": course.id, "name": course.name, "duration": course.duration} for course in courses
            if any(skill.strip().lower() in course.skills_required.lower() for skill in skills.split(','))
            and qualification in course.qualification_required.lower()
        ]

        return jsonify({"courses": matching_courses}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
#questions
@app.route('/questions', methods=['POST'])
def add_questions():
    data = request.get_json()  # This will return a list of questions
    if isinstance(data, list):  # Ensure the data is a list
        try:
            # Create multiple Question objects and add them to the session
            questions_to_add = [Question(question_text=text) for text in data if text]  # Filter out empty strings
            db.session.bulk_save_objects(questions_to_add)  # Efficient bulk insert
            db.session.commit()
            return jsonify({"message": "Questions added successfully"}), 201
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            return jsonify({"message": f"Error occurred: {str(e)}"}), 500
    else:
        return jsonify({"message": "Invalid input. Please send a list of questions."}), 400




if __name__ == '__main__':
    app.run(debug=True)
