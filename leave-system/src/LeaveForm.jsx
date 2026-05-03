import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // ใช้ CSS พื้นฐาน

function LeaveForm({ user, onSuccess }) {
  const [formData, setFormData] = useState({
    employeeId: user ? user.emp_code : '', // ดึงรหัสจากคนที่ล็อกอินเข้ามาจริงๆ
    leaveType: 'ลาป่วย', // ค่าเริ่มต้น
    startDate: '',
    endDate: '',
    reason: ''
  });
  const [certificate, setCertificate] = useState(null);

  const todayStr = new Date().toLocaleDateString('en-CA'); // Gets YYYY-MM-DD
  const isPastLeave = formData.startDate && formData.startDate < todayStr;
  const requiresCert = formData.leaveType === 'ลาป่วย' && isPastLeave;

  const minStartDate = formData.leaveType === 'ลาป่วย' ? undefined : todayStr;

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (requiresCert && !certificate) {
      alert("กรุณาแนบใบรับรองแพทย์สำหรับการลาป่วยย้อนหลัง");
      return;
    }

    try {
      const data = new FormData();
      data.append('employeeId', formData.employeeId);
      data.append('leaveType', formData.leaveType);
      data.append('startDate', formData.startDate);
      data.append('endDate', formData.endDate);
      data.append('reason', formData.reason);
      if (certificate) {
        data.append('certificate', certificate);
      }

      const response = await axios.post('http://localhost:8000/api/leaves', data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert('ส่งคำขอลาสำเร็จ รอหัวหน้าอนุมัติ');
      if (onSuccess) onSuccess();
    } catch (error) {
      console.error('เกิดข้อผิดพลาด:', error);
      alert(error.response?.data?.detail || 'ไม่สามารถส่งคำขอได้');
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
          <input type="date" name="startDate" required min={minStartDate} value={formData.startDate} onChange={handleChange} />
        </div>

        <div>
          <label>ถึงวันที่: </label>
          <input type="date" name="endDate" required min={formData.startDate || minStartDate} value={formData.endDate} onChange={handleChange} />
        </div>

        <div>
          <label>เหตุผล: </label>
          <textarea name="reason" required value={formData.reason} onChange={handleChange}></textarea>
        </div>

        {requiresCert && (
          <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#ffebee', borderRadius: '5px' }}>
            <label style={{ color: '#c62828', fontWeight: 'bold' }}>แนบใบรับรองแพทย์ (บังคับ): </label>
            <input 
              type="file" 
              accept=".png,.jpg,.jpeg,.pdf" 
              required 
              onChange={(e) => setCertificate(e.target.files[0])} 
              style={{ marginTop: '5px' }}
            />
          </div>
        )}

        <button type="submit" className="btn-primary" style={{ marginTop: '15px' }}>ส่งคำขอลา</button>
      </form>
    </div>
  );
}

export default LeaveForm;