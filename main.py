from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import jwt
import bcrypt
import os
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# ---------------- AUTH MIDDLEWARE ----------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({"error": "Token required"}), 401
        
        try:
            token = auth_header.split()[1]  # Bearer <token>
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        return f(*args, **kwargs)
    return decorated


# ---------------- REGISTER ROUTE ----------------
@app.post('/api/register')
def register():
    data = request.get_json()

    if not data.get("email"):
        return {"error": "email required"}, 400
    if not data.get("password"):
        return {"error": "password required"}, 400

    if User.query.filter_by(email=data["email"]).first():
        return {"error": "Email already registered"}, 400

    hashed_pwd = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
    user = User(email=data["email"], password=hashed_pwd.decode())
    db.session.add(user)
    db.session.commit()

    return {"message": "User registered successfully"}, 201


# ---------------- LOGIN ROUTE ----------------
@app.post("/api/login")
def login():
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"message": "Email & password required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    if not bcrypt.checkpw(data["password"].encode(), user.password.encode()):
        return jsonify({"message": "Invalid credentials"}), 401

    token = jwt.encode(
        {"email": user.email, "exp": datetime.utcnow() + timedelta(hours=1)},
        app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    return jsonify({"token": token}), 200

# ---------------- EMPLOYEE MODEL ----------------
class Employee(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(50))
    role = db.Column(db.String(50))
    date_joined = db.Column(db.Date, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "role": self.role,
            "date_joined": self.date_joined.isoformat()
        }


# ---------------- CRUD ENDPOINTS ----------------

# Create Employee
@app.post("/api/employees")
@token_required
def create_employee():
    data = request.get_json()
    if not data or "name" not in data or "email" not in data:
        return jsonify({"error": "name and email are required"}), 400

    if Employee.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    emp = Employee(
        name=data["name"],
        email=data["email"],
        department=data.get("department"),
        role=data.get("role")
    )
    db.session.add(emp)
    db.session.commit()
    return jsonify(emp.to_dict()), 201


# List Employees with Filtering + Pagination
@app.get("/api/employees/")
@token_required
def list_employees():
    query = Employee.query

    # Filtering
    department = request.args.get("department")
    role = request.args.get("role")
    if department:
        query = query.filter_by(department=department)
    if role:
        query = query.filter_by(role=role)

    # Pagination
    page = int(request.args.get("page", 1))
    per_page = 10
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "results": [emp.to_dict() for emp in paginated.items],
        "page": page,
        "total": paginated.total,
        "pages": paginated.pages
    }), 200


# Retrieve Employee
@app.get("/api/employees/<emp_id>/")
@token_required
def get_employee(emp_id):
    emp = Employee.query.get(emp_id)
    if not emp:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(emp.to_dict()), 200


# Update Employee
@app.put("/api/employees/<emp_id>/")
@token_required
def update_employee(emp_id):
    emp = Employee.query.get(emp_id)
    if not emp:
        return jsonify({"error": "Employee not found"}), 404

    data = request.get_json()
    if "email" in data:
        exists = Employee.query.filter(Employee.email == data["email"], Employee.id != emp_id).first()
        if exists:
            return jsonify({"error": "Email already taken"}), 400

    emp.name = data.get("name", emp.name)
    emp.email = data.get("email", emp.email)
    emp.department = data.get("department", emp.department)
    emp.role = data.get("role", emp.role)

    db.session.commit()
    return jsonify(emp.to_dict()), 200


# Delete Employee
@app.delete("/api/employees/<emp_id>/")
@token_required
def delete_employee(emp_id):
    emp = Employee.query.get(emp_id)
    if not emp:
        return jsonify({"error": "Employee not found"}), 404

    db.session.delete(emp)
    db.session.commit()
    return jsonify("employees deleted "), 204 


# ---------------- MAIN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=5000)
