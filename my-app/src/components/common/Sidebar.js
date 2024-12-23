// src/components/Sidebar.js
import React from 'react';
import { Drawer, List, ListItem, ListItemText, ListItemIcon } from '@mui/material';
import { Home, LiveTv, Notifications, DirectionsCar, BarChart, Report, Settings } from '@mui/icons-material';
import './Sidebar.css';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import {Link as RouterLink} from 'react-router-dom';
import { Link } from '@mui/material';

const Sidebar = ({ isSidebarOpen, toggleSidebar,activeSection }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleItemClick = (section) => {
    if (isMobile) toggleSidebar(); // Auto-close sidebar on mobile after selection
  };

  const menuItems = [
    { text: 'Home', section: 'dashboard', icon: <Home /> ,link:'/'},
    { text: 'Live Feeds', section: 'liveFeeds', icon: <LiveTv /> ,link:'/liveFeeds'},
    { text: 'Alerts', section: 'alerts', icon: <Notifications />, link:'/alerts' },
    { text: 'Registered Vehicles', section: 'registeredVehicles', icon: <DirectionsCar /> ,link:'/registeredVehicles'},
    { text: 'Traffic Stats', section: 'trafficStats', icon: <BarChart /> , link:'/trafficStats'},
    { text: 'Overspeeding Reports', section: 'overspeedingReports', icon: <Report /> , link:'/overspeedingReports'},
    { text: 'Settings', section: 'settings', icon: <Settings />, link:'/settings' },
  ];

  return (
    <Drawer
      variant={isMobile ? 'temporary' : 'persistent'}
      open={isSidebarOpen}
      onClose={toggleSidebar}
      sx={{
        width: 240,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 240,
          top: '64px', // Ensure it appears below the header
        },
      }}
    >
      <List>
        {menuItems.map((item) => (
          <Link
          component={RouterLink}
          to={item.link}
          key={item.text}
          sx={{ textDecoration: 'none', color: 'inherit' }} // Remove underline and blue color
        >
          <ListItem
            button
            key={item.text}
            selected={activeSection === item.section}
            onClick={() => handleItemClick(item.section)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
          </Link>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;
