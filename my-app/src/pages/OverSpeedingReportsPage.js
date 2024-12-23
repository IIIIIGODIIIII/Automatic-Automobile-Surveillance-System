import React, { useState } from 'react'
import Header from '../components/common/Header';
import Sidebar from '../components/common/Sidebar';
import OverspeedingReports from '../components/OverspeedingReports';
import { Box } from '@mui/material';
import Footer from '../components/common/Footer';

export default function OverSpeedingReportsPage() {
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
          <Sidebar isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} activeSection='livefeeds' />
          </Box>
          <OverspeedingReports />
          {/* <LiveFeeds /> */}
        </Box>
        <Footer />
      </div>
    );
}
