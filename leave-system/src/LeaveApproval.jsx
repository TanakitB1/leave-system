import React, { useState, useEffect } from 'react';
import axios from 'axios';

function LeaveApproval({ user }) {
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchPendingLeaves = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/leaves/pending/${user.department_id}`);
      setPendingLeaves(response.data.data);
    } catch (error) {
      console.error('Error fetching pending leaves:', error);
      alert('ไม่สามารถดึงข้อมูลคำขอลาได้');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && user.department_id) {
      fetchPendingLeaves();
    }
  }, [user]);

  const handleUpdateStatus = async (leaveId, status) => {
    try {
      await axios.put(`http://localhost:8000/api/leaves/${leaveId}/status`, { status });
      alert(`อัปเดตสถานะเป็น ${status} สำเร็จ`);
      fetchPendingLeaves(); // Refresh the list
    } catch (error) {
      console.error('Error updating status:', error);
      alert('เกิดข้อผิดพลาดในการอัปเดตสถานะ');
    }
  };

  if (loading) return <p>กำลังโหลดข้อมูล...</p>;

  return (
    <div style={{ marginTop: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '10px', backgroundColor: '#fff' }}>
      <h3 style={{ borderBottom: '2px solid #4CAF50', paddingBottom: '10px' }}>รายการรออนุมัติ</h3>
      {pendingLeaves.length === 0 ? (
        <p style={{ color: '#888' }}>ไม่มีคำขอลาที่รออนุมัติ</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '15px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f2f2f2' }}>
              <th style={thStyle}>รหัสพนักงาน</th>
              <th style={thStyle}>ชื่อ-นามสกุล</th>
              <th style={thStyle}>ประเภทการลา</th>
              <th style={thStyle}>วันที่เริ่ม - วันที่สิ้นสุด</th>
              <th style={thStyle}>เหตุผล</th>
              <th style={thStyle}>จัดการ</th>
            </tr>
          </thead>
          <tbody>
            {pendingLeaves.map((leave) => (
              <tr key={leave.id} style={{ borderBottom: '1px solid #ddd' }}>
                <td style={tdStyle}>{leave.emp_code}</td>
                <td style={tdStyle}>{leave.first_name} {leave.last_name}</td>
                <td style={tdStyle}>{leave.leave_type}</td>
                <td style={tdStyle}>{new Date(leave.start_date).toLocaleDateString('th-TH')} - {new Date(leave.end_date).toLocaleDateString('th-TH')}</td>
                <td style={tdStyle}>{leave.reason}</td>
                <td style={tdStyle}>
                  <button 
                    onClick={() => handleUpdateStatus(leave.id, 'อนุมัติ')}
                    style={{ ...btnStyle, backgroundColor: '#4CAF50' }}
                  >
                    อนุมัติ
                  </button>
                  <button 
                    onClick={() => handleUpdateStatus(leave.id, 'ไม่อนุมัติ')}
                    style={{ ...btnStyle, backgroundColor: '#f44336' }}
                  >
                    ไม่อนุมัติ
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const thStyle = { padding: '10px', border: '1px solid #ddd', textAlign: 'left' };
const tdStyle = { padding: '10px', border: '1px solid #ddd' };
const btnStyle = { padding: '6px 12px', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '5px' };

export default LeaveApproval;
