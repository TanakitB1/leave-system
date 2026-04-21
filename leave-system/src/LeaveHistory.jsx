import React, { useState, useEffect } from 'react';
import axios from 'axios';

function LeaveHistory({ user }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/leaves/history/${user.emp_code}`);
        setHistory(response.data.data);
      } catch (error) {
        console.error('Error fetching history:', error);
        alert('ไม่สามารถดึงประวัติการลาได้');
      } finally {
        setLoading(false);
      }
    };

    if (user && user.emp_code) {
      fetchHistory();
    }
  }, [user]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'อนุมัติ': return '#4CAF50';
      case 'ไม่อนุมัติ': return '#f44336';
      default: return '#FF9800'; // รออนุมัติ
    }
  };

  if (loading) return <p>กำลังโหลดประวัติการลา...</p>;

  return (
    <div style={{ marginTop: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '10px', backgroundColor: '#fff' }}>
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
            </tr>
          </thead>
          <tbody>
            {history.map((leave) => (
              <tr key={leave.id} style={{ borderBottom: '1px solid #ddd' }}>
                <td style={tdStyle}>{leave.leave_type}</td>
                <td style={tdStyle}>{new Date(leave.start_date).toLocaleDateString('th-TH')} - {new Date(leave.end_date).toLocaleDateString('th-TH')}</td>
                <td style={tdStyle}>{leave.reason}</td>
                <td style={tdStyle}>{new Date(leave.created_at).toLocaleDateString('th-TH')}</td>
                <td style={{ ...tdStyle, fontWeight: 'bold', color: getStatusColor(leave.status) }}>
                  {leave.status}
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
