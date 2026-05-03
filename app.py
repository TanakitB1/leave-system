from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
import uuid
import shutil
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from datetime import date, datetime, timedelta
import bcrypt
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def reset_leave_balance_every_year():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        current_year = date.today().year
        cursor.execute("SELECT id FROM employees")
        employees = cursor.fetchall()
        for emp in employees:
            try:
                cursor.execute("""
                INSERT INTO leave_balances (employee_id, year, sick_leave_used, personal_leave_used, annual_leave_used)
                VALUES (%s, %s, 0, 0, 0)
                """, (emp[0], current_year))
            except mysql.connector.Error as err:
                if err.errno != 1062:
                    print(f"Error resetting balance: {err}")
        conn.commit()
        print(f"[{datetime.now()}] รีเซ็ตโควตาวันลาสำหรับปี {current_year} เรียบร้อยแล้ว")
    except Exception as e:
        print(f"Error in scheduled job: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_leave_balance_every_year, 'cron', month=1, day=1, hour=0, minute=1)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
from pydantic import BaseModel
from typing import Optional

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
    reject_reason: Optional[str] = None

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

def calculate_leave_days(start_date: date, end_date: date) -> int:
    if end_date < start_date: return 0
    return (end_date - start_date).days + 1

def check_leave_balance(cursor, employee_id: int, leave_type: str, request_days: int, current_year: int):
    cursor.execute("SELECT sick_leave_used, personal_leave_used, annual_leave_used FROM leave_balances WHERE employee_id = %s AND year = %s", (employee_id, current_year))
    balance = cursor.fetchone()
    
    if not balance:
        cursor.execute("INSERT INTO leave_balances (employee_id, year) VALUES (%s, %s)", (employee_id, current_year))
        sick_used, personal_used, annual_used = 0, 0, 0
    else:
        sick_used = balance[0] or 0
        personal_used = balance[1] or 0
        annual_used = balance[2] or 0

    cursor.execute("SELECT created_at FROM employees WHERE id = %s", (employee_id,))
    emp_info = cursor.fetchone()
    
    limits = {"ลาป่วย": 30, "ลากิจ": 3, "ลาพักร้อน": 6}
    
    if leave_type == "ลาพักร้อน":
        if emp_info and emp_info[0]:
            days_worked = (datetime.now() - emp_info[0]).days
            if days_worked < 365:
                raise HTTPException(status_code=400, detail="ไม่สามารถลาพักร้อนได้ เนื่องจากอายุงานยังไม่ครบ 1 ปี")
                
    if leave_type not in limits:
        raise HTTPException(status_code=400, detail="ประเภทการลาไม่ถูกต้อง")
        
    limit = limits[leave_type]
    
    if leave_type == "ลาป่วย": used, col = sick_used, "sick_leave_used"
    elif leave_type == "ลากิจ": used, col = personal_used, "personal_leave_used"
    elif leave_type == "ลาพักร้อน": used, col = annual_used, "annual_leave_used"
        
    if used + request_days > limit:
        raise HTTPException(status_code=400, detail=f"โควตาวัน{leave_type}ไม่เพียงพอ (เหลือ {limit - used} วัน)")
        
    return col, used + request_days

@app.post("/api/leaves")
async def create_leave_request(
    employeeId: str = Form(...),
    leaveType: str = Form(...),
    startDate: date = Form(...),
    endDate: date = Form(...),
    reason: str = Form(...),
    certificate: UploadFile = File(None)
):
    try:
        today = date.today()
        if startDate < today:
            if leaveType != "ลาป่วย":
                raise HTTPException(status_code=400, detail="การลาย้อนหลังอนุญาตให้เฉพาะ 'ลาป่วย' เท่านั้น")
            if not certificate or not certificate.filename:
                raise HTTPException(status_code=400, detail="การลาป่วยย้อนหลังต้องแนบใบรับรองแพทย์ด้วย")

        cert_path = None
        if certificate and certificate.filename:
            allowed_extensions = [".png", ".jpg", ".jpeg", ".pdf"]
            ext = os.path.splitext(certificate.filename)[1].lower()
            if ext not in allowed_extensions:
                raise HTTPException(status_code=400, detail="รูปแบบไฟล์ใบรับรองแพทย์ไม่ถูกต้อง (อนุญาตแค่ png, jpg, jpeg, pdf)")
            
            filename = f"{uuid.uuid4()}{ext}"
            filepath = os.path.join("uploads", filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(certificate.file, buffer)
            cert_path = filepath.replace("\\", "/")

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM employees WHERE emp_code = %s", (employeeId,))
        emp_result = cursor.fetchone()
        
        if not emp_result:
            raise HTTPException(status_code=404, detail="ไม่พบรหัสพนักงานนี้ในระบบ")
        
        emp_id = emp_result[0]
        
        request_days = calculate_leave_days(startDate, endDate)
        if request_days <= 0:
            raise HTTPException(status_code=400, detail="วันที่ลาไม่ถูกต้อง")
            
        leave_year = startDate.year
        col_to_update, new_used_val = check_leave_balance(cursor, emp_id, leaveType, request_days, leave_year)
        
        cursor.execute(f"UPDATE leave_balances SET {col_to_update} = %s WHERE employee_id = %s AND year = %s", (new_used_val, emp_id, leave_year))

        insert_query = """
        INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status, certificate_path)
        VALUES (%s, %s, %s, %s, %s, 'รออนุมัติ', %s)
        """
        cursor.execute(insert_query, (emp_id, leaveType, startDate, endDate, reason, cert_path))
        conn.commit()

        return {"message": "ส่งคำขอลาสำเร็จ", "leave_id": cursor.lastrowid}
    except HTTPException:
        raise
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
        SELECT lr.id, lr.leave_type, lr.start_date, lr.end_date, lr.reason, lr.status, lr.certificate_path,
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

        cursor.execute("SELECT employee_id, leave_type, start_date, end_date, status FROM leave_requests WHERE id = %s", (leave_id,))
        leave_req = cursor.fetchone()
        if not leave_req:
            raise HTTPException(status_code=404, detail="ไม่พบคำขอลาที่ต้องการ")
            
        old_status = leave_req[4]
        
        if old_status not in ["ไม่อนุมัติ", "ยกเลิก"] and update_data.status == "ไม่อนุมัติ":
            # Refund quota
            emp_id, l_type, l_year = leave_req[0], leave_req[1], leave_req[2].year
            days = calculate_leave_days(leave_req[2], leave_req[3])
            col = ""
            if l_type == "ลาป่วย": col = "sick_leave_used"
            elif l_type == "ลากิจ": col = "personal_leave_used"
            elif l_type == "ลาพักร้อน": col = "annual_leave_used"
            if col:
                cursor.execute(f"UPDATE leave_balances SET {col} = {col} - %s WHERE employee_id = %s AND year = %s", (days, emp_id, l_year))

        cursor.execute("UPDATE leave_requests SET status = %s, reject_reason = %s WHERE id = %s", 
                       (update_data.status, update_data.reject_reason, leave_id))
        conn.commit()

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
        SELECT lr.id, lr.leave_type, lr.start_date, lr.end_date, lr.reason, lr.status, lr.reject_reason, lr.certificate_path, lr.created_at
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

@app.delete("/api/leaves/{leave_id}")
async def delete_leave_request(leave_id: int, emp_code: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # ค้นหาคำขอลา และเช็คว่าเป็นของพนักงานคนนี้จริงไหม
        query = """
        SELECT lr.status, e.emp_code 
        FROM leave_requests lr
        JOIN employees e ON lr.employee_id = e.id
        WHERE lr.id = %s
        """
        cursor.execute(query, (leave_id,))
        leave_req = cursor.fetchone()

        if not leave_req:
            raise HTTPException(status_code=404, detail="ไม่พบคำขอลาที่ต้องการ")
            
        if leave_req["emp_code"] != emp_code:
            raise HTTPException(status_code=403, detail="คุณไม่มีสิทธิ์ลบคำขอลานี้")
            
        if leave_req["status"] != 'รออนุมัติ':
            raise HTTPException(status_code=400, detail="ไม่สามารถลบคำขอที่ถูกพิจารณาไปแล้วได้")

        # Refund quota
        cursor.execute("SELECT employee_id, leave_type, start_date, end_date FROM leave_requests WHERE id = %s", (leave_id,))
        l_req = cursor.fetchone()
        emp_id, l_type, l_year = l_req["employee_id"], l_req["leave_type"], l_req["start_date"].year
        days = calculate_leave_days(l_req["start_date"], l_req["end_date"])
        col = ""
        if l_type == "ลาป่วย": col = "sick_leave_used"
        elif l_type == "ลากิจ": col = "personal_leave_used"
        elif l_type == "ลาพักร้อน": col = "annual_leave_used"
        if col:
            cursor.execute(f"UPDATE leave_balances SET {col} = {col} - %s WHERE employee_id = %s AND year = %s", (days, emp_id, l_year))

        # เปลี่ยนสถานะคำขอลาเป็น 'ยกเลิก' แทนการลบข้อมูลทิ้ง
        cursor.execute("UPDATE leave_requests SET status = 'ยกเลิก' WHERE id = %s", (leave_id,))
        conn.commit()

        return {"message": "ยกเลิกคำขอลาสำเร็จ"}
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.get("/api/leaves/balance/{emp_code}")
async def get_leave_balance(emp_code: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        current_year = date.today().year
        
        cursor.execute("SELECT id FROM employees WHERE emp_code = %s", (emp_code,))
        emp = cursor.fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        emp_id = emp["id"]
        cursor.execute("SELECT sick_leave_used, personal_leave_used, annual_leave_used FROM leave_balances WHERE employee_id = %s AND year = %s", (emp_id, current_year))
        balance = cursor.fetchone()
        
        sick_used, personal_used, annual_used = (balance["sick_leave_used"], balance["personal_leave_used"], balance["annual_leave_used"]) if balance else (0, 0, 0)
            
        return {
            "sick_leave_balance": max(0, 30 - sick_used),
            "personal_leave_balance": max(0, 3 - personal_used),
            "annual_leave_balance": max(0, 6 - annual_used)
        }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()