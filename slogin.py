import os
import mysql.connector
import jwt
import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://localhost:3000",          # CRA (if used)
                   "https://student-lac-six.vercel.app" ],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Database API 🎓🚀"}

# Basic Auth
security = HTTPBasic()
VALID_USERNAME = "Jannu"
VALID_PASSWORD = "12345"

def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != VALID_USERNAME or credentials.password != VALID_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return credentials.username

@app.post("/check")
def get_secure_data(username: str = Depends(basic_auth)):
    return {"message": "Access granted", "username": username}

# Login Check
class LoginItem(BaseModel):
    username: str
    password: str

@app.post("/data")
def login_user(obj: LoginItem):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM login")
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    for db_username, db_password in results:
        if obj.username == db_username and obj.password == db_password:
            return {"status": "Success", "message": "Login successful"}
    return {"status": "Failure", "message": "Invalid username or password"}

# Insert Login
class User(BaseModel):
    username: str
    password: int

@app.post("/insert")
def insert_user(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO login (username, password) VALUES (%s, %s)"
    cursor.execute(query, (user.username, user.password))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Data inserted successfully"}

# Forgot Password
class ForgotPasswordRequest(BaseModel):
    username: str
    new_password: str

@app.post("/forgot_password")
def forgot_password(request: ForgotPasswordRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM login WHERE username = %s", (request.username,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("UPDATE login SET password = %s WHERE username = %s",
                   (request.new_password, request.username))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "Success", "message": "Password updated successfully"}

# Get Users
@app.get("/detail")
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detail")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {"sid": user[0], "name": user[1], "department": user[2], "sem": user[3], "cgpa": user[4]}
        for user in users
    ]

# Filter: Department
class DepartmentFilter(BaseModel):
    department: str

@app.post("/department")
def filter_by_department(obj: DepartmentFilter):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detail WHERE department = %s", (obj.department,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if results:
        return [
            {"sid": r[0], "name": r[1], "department": r[2], "sem": r[3], "cgpa": r[4]}
            for r in results
        ]
    return {"status": "Failure", "message": "No users found in that department"}

# Filter: Semester
class SemesterFilter(BaseModel):
    sem: int

@app.post("/sem")
def filter_by_sem(obj: SemesterFilter):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detail WHERE sem = %s", (obj.sem,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if results:
        return [
            {"sid": r[0], "name": r[1], "department": r[2], "sem": r[3], "cgpa": r[4]}
            for r in results
        ]
    return {"status": "Failure", "message": "No users found in that semester"}

# Filter: CGPA
class CgpaFilter(BaseModel):
    cgpa: int

@app.post("/cgpa")
def filter_by_cgpa(obj: CgpaFilter):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detail WHERE cgpa = %s", (obj.cgpa,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if results:
        return [
            {"sid": r[0], "name": r[1], "department": r[2], "sem": r[3], "cgpa": r[4]}
            for r in results
        ]
    return {"status": "Failure", "message": "No users found with that CGPA"}

# Search
class SearchQuery(BaseModel):
    search: str

@app.post("/search")
def search_users(query: SearchQuery):
    conn = get_db_connection()
    cursor = conn.cursor()
    search_term = f"%{query.search}%"
    sql = """
        SELECT * FROM detail
        WHERE name LIKE %s OR sid LIKE %s OR department LIKE %s OR sem LIKE %s OR cgpa LIKE %s
    """
    cursor.execute(sql, (search_term,)*5)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {"sid": r[0], "name": r[1], "department": r[2], "sem": r[3], "cgpa": r[4]}
        for r in results
    ] if results else []

# Register Student
class UserRegistration(BaseModel):
    sid: int
    name: str
    department: str
    sem: int
    cgpa: int

@app.post("/register")
def register_user(user: UserRegistration):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO detail (sid, name, department, sem, cgpa) VALUES (%s, %s, %s, %s, %s)",
        (user.sid, user.name, user.department, user.sem, user.cgpa)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "User registered successfully!"}

# Knock Token
@app.get("/knock-token")
def generate_knock_token():
    private_key = os.getenv("KNOCK_SIGNING_PRIVATE_KEY").replace('\\n', '\n')
    payload = {
        "sub": "Jannu",
        "iat": int(datetime.datetime.utcnow().timestamp()),
        "exp": int((datetime.datetime.utcnow() + datetime.timedelta(days=1)).timestamp()),
    }

    try:
        token = jwt.encode(payload, private_key, algorithm="RS256")
        print("✅ Token generated:\n", token)
    except Exception as e:
        print("❌ Error:", e)
