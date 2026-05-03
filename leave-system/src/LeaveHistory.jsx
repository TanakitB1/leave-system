import React, { useState, useEffect } from 'react';
import axios from 'axios';

function LeaveHistory({ user }) {
  const [history, setHistory] = useState([]);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const historyRes = await axios.get(`http://localhost:8000/api/leaves/history/${user.emp_code}`);
        setHistory(historyRes.data.data);
        const balanceRes = await axios.get(`http://localhost:8000/api/leaves/balance/${user.emp_code}`);
        setBalance(balanceRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
        alert('ไม่สามารถดึงข้อมูลได้');
      } finally {
        setLoading(false);
      }
    };

    if (user && user.emp_code) {
      fetchData();
    }
  }, [user]);

  const handleDelete = async (leaveId) => {
    if (!window.confirm("คุณแน่ใจหรือไม่ที่จะยกเลิกคำขอลานี้?")) return;
    
    try {
      await axios.delete(`http://localhost:8000/api/leaves/${leaveId}?emp_code=${user.emp_code}`);
      alert('ยกเลิกคำขอลาสำเร็จ');
      // เปลี่ยนสถานะใน state เป็น 'ยกเลิก' แทนการลบแถวทิ้ง
      setHistory(history.map(item => item.id === leaveId ? { ...item, status: 'ยกเลิก' } : item));
    } catch (error) {
      console.error('Error deleting leave:', error);
      alert(error.response?.data?.detail || 'เกิดข้อผิดพลาดในการยกเลิกคำขอ');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'อนุมัติ': return '#4CAF50';
      case 'ไม่อนุมัติ': return '#f44336';
      case 'ยกเลิก': return '#9e9e9e'; // สีเทา
      default: return '#FF9800'; // รออนุมัติ
    }
  };

  if (loading) return <p>กำลังโหลดข้อมูล...</p>;

  return (
    <div style={{ marginTop: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '10px', backgroundColor: '#fff' }}>
      {balance && (
        <div style={{ display: 'flex', gap: '15px', marginBottom: '20px' }}>
          <div style={{ flex: 1, padding: '15px', backgroundColor: '#e3f2fd', borderRadius: '8px', textAlign: 'center' }}>
            <h4 style={{ margin: 0, color: '#555' }}>ลาป่วยคงเหลือ</h4>
            <h2 style={{ color: '#1976d2', margin: '10px 0 0 0' }}>{balance.sick_leave_balance} วัน</h2>
          </div>
          <div style={{ flex: 1, padding: '15px', backgroundColor: '#fff3e0', borderRadius: '8px', textAlign: 'center' }}>
            <h4 style={{ margin: 0, color: '#555' }}>ลากิจคงเหลือ</h4>
            <h2 style={{ color: '#f57c00', margin: '10px 0 0 0' }}>{balance.personal_leave_balance} วัน</h2>
          </div>
          <div style={{ flex: 1, padding: '15px', backgroundColor: '#e8f5e9', borderRadius: '8px', textAlign: 'center' }}>
            <h4 style={{ margin: 0, color: '#555' }}>ลาพักร้อนคงเหลือ</h4>
            <h2 style={{ color: '#388e3c', margin: '10px 0 0 0' }}>{balance.annual_leave_balance} วัน</h2>
          </div>
        </div>
      )}
      <h3 style={{ borderBottom: '2px solid #2196F3', paddingBottom: '10px' }}>ประวัติการลาของฉัน</h3>
      {history.length === 0 ? (
        <p style={{ color: '#888' }}>คุณยังไม่มีประวัติการลา</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '15px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f2f2f2' }}>
              <th style={thStyle}>ประเภทการลา</th>
              <th style={thStyle}>วันที่เริ่ม - วันที่สิ้นสุด</th>
              <th style={thStyle}>เหตุผล</th>
              <th style={thStyle}>วันที่ยื่นขอ</th>
              <th style={thStyle}>สถานะ</th>
              <th style={thStyle}>จัดการ</th>
            </tr>
          </thead>
          <tbody>
            {history.map((leave) => (
              <tr key={leave.id} style={{ borderBottom: '1px solid #ddd' }}>
                <td style={tdStyle}>
                  {leave.leave_type}
                  {leave.certificate_path && (
                    <div style={{ marginTop: '5px' }}>
                      <a href={`http://localhost:8000/${leave.certificate_path}`} target="_blank" rel="noreferrer" style={{ fontSize: '0.85em', color: '#1976d2', textDecoration: 'none' }}>
                        📄 ดูใบรับรองแพทย์
                      </a>
                    </div>
                  )}
                </td>
                <td style={tdStyle}>{new Date(leave.start_date).toLocaleDateString('th-TH')} - {new Date(leave.end_date).toLocaleDateString('th-TH')}</td>
                <td style={tdStyle}>{leave.reason}</td>
                <td style={tdStyle}>{new Date(leave.created_at).toLocaleDateString('th-TH')}</td>
                <td style={{ ...tdStyle, fontWeight: 'bold', color: getStatusColor(leave.status) }}>
                  {leave.status}
                  {leave.status === 'ไม่อนุมัติ' && leave.reject_reason && (
                    <div style={{ fontSize: '0.85em', color: '#555', marginTop: '5px', fontWeight: 'normal' }}>
                      เหตุผล: {leave.reject_reason}
                    </div>
                  )}
                </td>
                <td style={tdStyle}>
                  {leave.status === 'รออนุมัติ' && (
                    <button 
                      onClick={() => handleDelete(leave.id)}
                      style={{ padding: '5px 10px', backgroundColor: '#f44336', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
                    >
                      ยกเลิก
                    </button>
                  )}
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

export default LeaveHistory;
