import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // ใช้ CSS พื้นฐาน

function LeaveForm({ user }) {
  const [formData, setFormData] = useState({
    employeeId: user ? user.emp_code : '', // ดึงรหัสจากคนที่ล็อกอินเข้ามาจริงๆ
    leaveType: 'ลาป่วย', // ค่าเริ่มต้น
    startDate: '',
    endDate: '',
    reason: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
  try {
      // เอาเครื่องหมาย // ด้านหน้าออก และเปลี่ยนพอร์ตจาก 5000 เป็น 8000
      const response = await axios.post('http://localhost:8000/api/leaves', formData);
      console.log('ส่งข้อมูลการลาสำเร็จ:', formData);
      alert('ส่งคำขอลาสำเร็จ รอหัวหน้าอนุมัติ');
    } catch (error) {
      console.error('เกิดข้อผิดพลาด:', error);
      alert('ไม่สามารถส่งคำขอได้');
    }
  };


  return (
    <div className="leave-form-container">
      <h2>แบบฟอร์มขออนุญาตลา</h2>
      <form onSubmit={handleSubmit}>
        
        <div>
          <label>ประเภทการลา: </label>
          <select name="leaveType" value={formData.leaveType} onChange={handleChange}>
            <option value="ลาป่วย">ลาป่วย</option>
            <option value="ลากิจ">ลากิจ</option>
            <option value="ลาพักร้อน">ลาพักร้อน</option>
          </select>
        </div>

        <div>
          <label>วันที่เริ่ม: </label>
          <input type="date" name="startDate" required value={formData.startDate} onChange={handleChange} />
        </div>

        <div>
          <label>ถึงวันที่: </label>
          <input type="date" name="endDate" required value={formData.endDate} onChange={handleChange} />
        </div>

        <div>
          <label>เหตุผล: </label>
          <textarea name="reason" required value={formData.reason} onChange={handleChange}></textarea>
        </div>

        <button type="submit" className="btn-primary" style={{ marginTop: '15px' }}>ส่งคำขอลา</button>
      </form>
    </div>
  );
}

export default LeaveForm;