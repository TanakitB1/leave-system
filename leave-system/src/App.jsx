import React, { useState } from 'react';
import axios from 'axios';
import LeaveForm from './LeaveForm';
import AddEmployee from './AddEmployee';
import LeaveHistory from './LeaveHistory';
import LeaveApproval from './LeaveApproval';
import './App.css'; // Make sure to import CSS

function App() {
  const [user, setUser] = useState(null);
  const [loginInput, setLoginInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [activeTab, setActiveTab] = useState('home'); // 'home', 'leave', 'approve', 'manage'

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:8000/api/login', {
        emp_code: loginInput.trim().toUpperCase(),
        password: passwordInput
      });
      setUser(response.data.user);
      // Set default tab based on role
      setActiveTab(response.data.user.role === 'manager' ? 'approve' : 'home');
    } catch (error) {
      alert(error.response?.data?.detail || 'รหัสพนักงานหรือรหัสผ่านไม่ถูกต้อง');
    }
  };

  const handleLogout = () => {
    setUser(null);
    setLoginInput('');
    setPasswordInput('');
  };

  // 1. หน้าจอ Login
  if (!user) {
    return (
      <div className="login-container">
        <div className="login-box glass-effect">
          <div className="company-logo">
            <h1>🏢 บริษัท ตั้งหวังเจ้ง</h1>
            <p>ระบบจัดการทรัพยากรบุคคล (HRMS)</p>
          </div>
          <h2>เข้าสู่ระบบ</h2>
          <form onSubmit={handleLogin} className="login-form">
            <div className="input-group">
              <label>รหัสพนักงาน</label>
              <input 
                type="text" 
                placeholder="เช่น 000001, 100001" 
                value={loginInput}
                onChange={(e) => setLoginInput(e.target.value)}
                required
              />
            </div>
            <div className="input-group">
              <label>รหัสผ่าน</label>
              <input 
                type="password" 
                placeholder="กรอกรหัสผ่าน" 
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary">
              ล็อกอินเข้าสู่ระบบ
            </button>
          </form>
        </div>
      </div>
    );
  }

  // 2. หน้าจอหลังเข้าระบบแล้ว (มี Navbar)
  return (
    <div className="app-container">
      {/* Navbar */}
      <nav className="navbar">
        <div className="nav-brand">
          <h1>🏢 ตั้งหวังเจ้ง</h1>
        </div>
        
        <div className="nav-menu">
          {user.role === 'employee' && (
            <>
              <button 
                className={`nav-item ${activeTab === 'home' ? 'active' : ''}`}
                onClick={() => setActiveTab('home')}
              >
                ประวัติการลา
              </button>
              <button 
                className={`nav-item ${activeTab === 'leave' ? 'active' : ''}`}
                onClick={() => setActiveTab('leave')}
              >
                ยื่นคำขอลา
              </button>
            </>
          )}

          {user.role === 'manager' && (
            <>
              <button 
                className={`nav-item ${activeTab === 'approve' ? 'active' : ''}`}
                onClick={() => setActiveTab('approve')}
              >
                รออนุมัติ
              </button>
              <button 
                className={`nav-item ${activeTab === 'manage' ? 'active' : ''}`}
                onClick={() => setActiveTab('manage')}
              >
                จัดการพนักงาน
              </button>
            </>
          )}
        </div>

        <div className="nav-user">
          <div className="user-info">
            <span className="user-name">{user.first_name} {user.last_name}</span>
            <span className="user-role badge-role">{user.role === 'manager' ? 'หัวหน้า' : 'พนักงาน'}</span>
            {user.department_name && (
              <span className="user-dept badge-dept">{user.department_name}</span>
            )}
          </div>
          <button onClick={handleLogout} className="btn-logout">ออกจากระบบ</button>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="main-content">
        {user.role === 'employee' && activeTab === 'home' && (
          <div className="fade-in">
            <LeaveHistory user={user} />
          </div>
        )}
        {user.role === 'employee' && activeTab === 'leave' && (
          <div className="fade-in">
            <LeaveForm user={user} />
          </div>
        )}

        {user.role === 'manager' && activeTab === 'approve' && (
          <div className="fade-in">
            <LeaveApproval user={user} />
          </div>
        )}
        {user.role === 'manager' && activeTab === 'manage' && (
          <div className="fade-in">
            <AddEmployee />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;