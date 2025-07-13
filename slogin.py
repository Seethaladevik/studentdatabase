import mysql.connector
import uvicorn
import os
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Connection
# def get_db_connection():
#     connection = mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="",
#         database="register",
#         port="3306"
#     )
#     return connection
def get_db_connection():
    connection = mysql.connector.connect(
        host="auth-db1834.hstgr.io",
        user="u651328475_fastapi",
        password="U651328475_fastapi",
        database="u651328475_fastapi"


    )
    return connection
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("slogin:app", host="0.0.0.0", port=port, reload=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Database API 🎓🚀"}

# Basic Auth
security = HTTPBasic()
VALID_USERNAME = "Jannu"
VALID_PASSWORD = "12345"

def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != VALID_USERNAME or credentials.password != VALID_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Secure Route
@app.post("/check")
def get_secure_data(username: str = Depends(basic_auth)):
    return {"message": "Access granted", "username": username}

# Login Validation
class LoginItem(BaseModel):
    username: str
    password: int

@app.post("/data")
def read_root2(obj: LoginItem):
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

# Insert Login Credentials
class User(BaseModel):
    username: str
    password: str

@app.post("/insert")
def insert_data(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO login (username, password) VALUES (%s, %s)"
    values = (user.username, user.password)
    cursor.execute(query, values)
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

# Get All Users from Detail Table
@app.get("/detail")
def get_users():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM detail")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return [
        {"sid": user[0], "name": user[1], "department": user[2], "sem": user[3], "cgpa": user[4]}
        for user in users
    ]

# Filter by Department
class DepartmentFilter(BaseModel):
    department: str

@app.post("/department")
def filter_by_department(obj: DepartmentFilter):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM detail WHERE department = %s"
    cursor.execute(query, (obj.department,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if results:
        return [
            {"sid": user[0], "name": user[1], "department": user[2], "sem": user[3], "cgpa": user[4]}
            for user in results
        ]
    return {"status": "Failure", "message": "No users found in the specified department"}

# Filter by Semester
class SemesterFilter(BaseModel):
    sem: int

@app.post("/sem")
def filter_by_sem(obj: SemesterFilter):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM detail WHERE sem = %s"
    cursor.execute(query, (obj.sem,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if results:
        return [
            {"sid": user[0], "name": user[1], "department": user[2], "sem": user[3], "cgpa": user[4]}
            for user in results
        ]
    return {"status": "Failure", "message": "No users found for the specified semester"}

# Filter by CGPA
class CgpaFilter(BaseModel):
    cgpa: int

@app.post("/cgpa")
def filter_by_cgpa(obj: CgpaFilter):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM detail WHERE cgpa = %s"
    cursor.execute(query, (obj.cgpa,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if results:
        return [
            {"sid": user[0], "name": user[1], "department": user[2], "sem": user[3], "cgpa": user[4]}
            for user in results
        ]
    return {"status": "Failure", "message": "No users found with the specified CGPA"}

# Search API
class SearchQuery(BaseModel):
    search: str

@app.post("/search")
def search_users(query: SearchQuery):
    conn = get_db_connection()
    cursor = conn.cursor()
    search_term = f"%{query.search}%"
    sql_query = """
        SELECT * FROM detail
        WHERE sname LIKE %s
        OR sid LIKE %s
        OR department LIKE %s
        OR sem LIKE %s
        OR cgpa LIKE %s
    """
    cursor.execute(sql_query, (search_term, search_term, search_term, search_term, search_term))
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if not results:
        return []

    return [
        {"sid": user[0], "name": user[1], "department": user[2], "sem": user[3], "cgpa": user[4]}
        for user in results
    ]

# Register new user to 'detail' table
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
    query = "INSERT INTO detail (sid, name, department, sem, cgpa) VALUES (%s, %s, %s, %s, %s)"
    values = (user.sid, user.name, user.department, user.sem, user.cgpa)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "User registered successfully!"}
