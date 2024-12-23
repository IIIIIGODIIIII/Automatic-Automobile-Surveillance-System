import React, { useState } from 'react'
import Header from '../components/common/Header';
import { Box } from '@mui/material';
import Sidebar from '../components/common/Sidebar';
import Footer from '../components/common/Footer';
import TrafficStatsGraph from '../components/TrafficStatsGraph';

function TrafficStatsPage() {
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
          <TrafficStatsGraph />
          {/* <LiveFeeds /> */}
        </Box>
        <Footer />
      </div>
    );
}

export default TrafficStatsPage
