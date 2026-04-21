import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AddEmployee() {
  const [departments, setDepartments] = useState([]);
  const [empData, setEmpData] = useState({
    first_name: '',
    last_name: '',
    role: 'employee',
    password: '',
    department_id: ''
  });

  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/departments');
        setDepartments(response.data.data);
        if (response.data.data.length > 0) {
          setEmpData(prev => ({ ...prev, department_id: response.data.data[0].id }));
        }
      } catch (error) {
        console.error('Error fetching departments:', error);
      }
    };
    fetchDepartments();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:8000/api/employees', empData);
      // แสดง Alert ที่มีรหัสพนักงานใหม่บอกด้วย
      alert(response.data.message); 
      // 2. ล้างค่าฟอร์ม
      setEmpData({ first_name: '', last_name: '', role: 'employee', password: '', department_id: departments[0]?.id || '' });
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || 'เกิดข้อผิดพลาดในการเพิ่มพนักงาน');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '0 auto' }}>
      <h2>เพิ่มพนักงานใหม่</h2>
      <form onSubmit={handleSubmit}>
        
        {/* 3. ลบ <div> ที่เป็นช่องกรอกรหัสพนักงานทิ้งไปเลยครับ เริ่มที่ชื่อได้เลย */}
        
        <div style={{ marginBottom: '10px' }}>
          <label>ชื่อ:</label><br/>
          <input type="text" value={empData.first_name} onChange={(e) => setEmpData({...empData, first_name: e.target.value})} required />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label>นามสกุล:</label><br/>
          <input type="text" value={empData.last_name} onChange={(e) => setEmpData({...empData, last_name: e.target.value})} required />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label>ตั้งรหัสผ่าน:</label><br/>
          <input type="password" value={empData.password} onChange={(e) => setEmpData({...empData, password: e.target.value})} required />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label>แผนก:</label><br/>
          <select value={empData.department_id} onChange={(e) => setEmpData({...empData, department_id: parseInt(e.target.value)})}>
            {departments.map(dept => (
              <option key={dept.id} value={dept.id}>{dept.name}</option>
            ))}
          </select>
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label>ตำแหน่ง:</label><br/>
          <select value={empData.role} onChange={(e) => setEmpData({...empData, role: e.target.value})}>
            <option value="employee">พนักงาน (Employee)</option>
            <option value="manager">หัวหน้า (Manager)</option>
          </select>
        </div>
        <button type="submit" style={{ backgroundColor: '#4CAF50', color: 'white', padding: '10px 20px', border: 'none', cursor: 'pointer' }}>
          บันทึกรายชื่อ
        </button>
      </form>
    </div>
  );
}

export default AddEmployee;