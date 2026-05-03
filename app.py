from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from datetime import date
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""), 
    "database": os.getenv("DB_NAME", "leave_system_db")
}

# --- Models ---
class LeaveRequest(BaseModel):
    employeeId: str
    leaveType: str
    startDate: date
    endDate: date
    reason: str

class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    role: str
    password: str
    department_id: int

class LoginRequest(BaseModel):
    emp_code: str
    password: str  # เพิ่มการรับรหัสผ่านตอนล็อกอิน

class LeaveStatusUpdate(BaseModel):
    status: str

# --- APIs ---
@app.get("/")
def read_root():
    return {"message": "เซิร์ฟเวอร์ระบบลาทำงานปกติจ้า!"}

@app.post("/api/login")
async def login(req: LoginRequest):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # ค้นหาด้วย emp_code เพื่อนำ hashed password มาตรวจสอบ
        cursor.execute(
            """
            SELECT e.emp_code, e.first_name, e.last_name, e.role, e.department_id, e.password, d.name AS department_name
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            WHERE e.emp_code = %s
            """, 
            (req.emp_code,)
        )
        user = cursor.fetchone()

        # ตรวจสอบรหัสผ่านที่ส่งมากับรหัสผ่านที่ถูก hash ไว้ในฐานข้อมูล
        if user and verify_password(req.password, user["password"]):
            # ไม่ส่ง password กลับไปให้ client เพื่อความปลอดภัย
            del user["password"]
            return {"message": "Login Success", "user": user}
        else:
            raise HTTPException(status_code=401, detail="รหัสพนักงานหรือรหัสผ่านไม่ถูกต้อง")
            
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.post("/api/leaves")
async def create_leave_request(leave: LeaveRequest):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM employees WHERE emp_code = %s", (leave.employeeId,))
        emp_result = cursor.fetchone()
        
        if not emp_result:
            raise HTTPException(status_code=404, detail="ไม่พบรหัสพนักงานนี้ในระบบ")
        
        emp_id = emp_result[0]

        insert_query = """
        INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status)
        VALUES (%s, %s, %s, %s, %s, 'รออนุมัติ')
        """
        cursor.execute(insert_query, (emp_id, leave.leaveType, leave.startDate, leave.endDate, leave.reason))
        conn.commit()

        return {"message": "ส่งคำขอลาสำเร็จ", "leave_id": cursor.lastrowid}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.post("/api/employees")
async def add_employee(emp: EmployeeCreate):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check for existing manager in the department
        if emp.role == 'manager':
            cursor.execute("SELECT id FROM employees WHERE department_id = %s AND role = 'manager'", (emp.department_id,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="แผนกนี้มีหัวหน้าอยู่แล้ว ไม่สามารถเพิ่มหัวหน้าซ้ำได้")

        # Generate 6-digit code
        prefix = "0" if emp.role == "manager" else "1"
        cursor.execute("SELECT emp_code FROM employees WHERE emp_code LIKE %s ORDER BY emp_code DESC LIMIT 1", (f"{prefix}%",))
        last_emp = cursor.fetchone()

        if last_emp and last_emp[0]:
            last_code = last_emp[0]
            next_number = int(last_code) + 1
            new_emp_code = f"{next_number:06d}"
        else:
            new_emp_code = f"{prefix}00001"

        # แฮชรหัสผ่านก่อนบันทึกลงฐานข้อมูล
        hashed_pwd = hash_password(emp.password)

        sql = """
            INSERT INTO employees (emp_code, first_name, last_name, role, password, department_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (new_emp_code, emp.first_name, emp.last_name, emp.role, hashed_pwd, emp.department_id)
        
        cursor.execute(sql, values)
        conn.commit()

        return {"message": f"เพิ่มพนักงาน {emp.first_name} สำเร็จ! รหัสที่ได้คือ {new_emp_code}"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.get("/api/departments")
async def get_departments():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM departments")
        return {"data": cursor.fetchall()}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.get("/api/leaves/pending/{department_id}")
async def get_pending_leaves(department_id: int):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT lr.id, lr.leave_type, lr.start_date, lr.end_date, lr.reason, lr.status, 
               e.first_name, e.last_name, e.emp_code
        FROM leave_requests lr
        JOIN employees e ON lr.employee_id = e.id
        WHERE lr.status = 'รออนุมัติ' AND e.department_id = %s
        ORDER BY lr.created_at ASC
        """
        cursor.execute(query, (department_id,))
        leaves = cursor.fetchall()
        return {"data": leaves}
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.put("/api/leaves/{leave_id}/status")
async def update_leave_status(leave_id: int, update_data: LeaveStatusUpdate):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        if update_data.status not in ["อนุมัติ", "ไม่อนุมัติ"]:
            raise HTTPException(status_code=400, detail="สถานะไม่ถูกต้อง")

        cursor.execute("UPDATE leave_requests SET status = %s WHERE id = %s", (update_data.status, leave_id))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบคำขอลาที่ต้องการ")

        return {"message": f"อัปเดตสถานะเป็น {update_data.status} สำเร็จ"}
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.get("/api/leaves/history/{emp_code}")
async def get_leave_history(emp_code: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT lr.id, lr.leave_type, lr.start_date, lr.end_date, lr.reason, lr.status, lr.created_at
        FROM leave_requests lr
        JOIN employees e ON lr.employee_id = e.id
        WHERE e.emp_code = %s
        ORDER BY lr.created_at DESC
        """
        cursor.execute(query, (emp_code,))
        history = cursor.fetchall()
        return {"data": history}
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()