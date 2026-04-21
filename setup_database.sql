-- Drop database if it exists to reset everything
DROP DATABASE IF EXISTS leave_system_db;

-- Create Database
CREATE DATABASE leave_system_db;
USE leave_system_db;

-- Create Departments Table
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Create Employees Table
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_code VARCHAR(10) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'employee',
    password VARCHAR(255) NOT NULL DEFAULT '123456',
    department_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- Create Leave Requests Table
CREATE TABLE IF NOT EXISTS leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    leave_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(50) DEFAULT 'รออนุมัติ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Insert Departments
INSERT INTO departments (name) VALUES 
('ไอที (IT)'),
('บุคคล (HR)'),
('การตลาด (Marketing)');

-- Insert Mock Employees (Managers start with 0, Employees start with 1, 6 digits)
-- หัวหน้าแผนก (Manager)
INSERT INTO employees (emp_code, first_name, last_name, role, password, department_id) VALUES 
('000001', 'วีระ', 'ผลิด', 'manager', '123456', 1),
('000002', 'นิดา', 'สวย', 'manager', '123456', 2),
('000003', 'อนันต์', 'เมืองไทย', 'manager', '123456', 3);

-- พนักงาน (Employee)
INSERT INTO employees (emp_code, first_name, last_name, role, password, department_id) VALUES 
('100001', 'สมชาย', 'ใจดี', 'employee', '123456', 1),
('100002', 'สมหญิง', 'ใจใหญ่', 'employee', '123456', 1),
('100003', 'ปัญญา', 'เก่ง', 'employee', '123456', 2),
('100004', 'ธนัต', 'สวย', 'employee', '123456', 3),
('100005', 'นารี', 'หวัง', 'employee', '123456', 3);
