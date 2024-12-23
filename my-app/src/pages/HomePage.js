import React, { useState } from 'react';
import Header from '../components/common/Header';
import Sidebar from '../components/common/Sidebar';
import Footer from '../components/common/Footer';
import { Box } from '@mui/material';
import Dashboard from '../components/dashboard/Dashboard';

function HomePage() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };
  return (
    <div className="app">
      <Header toggleSidebar={toggleSidebar} />

      {/* Main layout container */}
      <Box sx={{ display: 'flex' }}>
        {/* Sidebar */}
        <Box display={isSidebarOpen?'block':'none'}>
        <Sidebar isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} activeSection='dashboard' />
        </Box>
        <Dashboard />
      </Box>
      <Footer />
    </div>
  );
}

export default HomePage
