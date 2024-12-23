// src/components/Header.js
import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

const Header = ({ toggleSidebar }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <AppBar position="static" sx={{bgcolor:'#2c3e50'}}>
      <Toolbar>
        {/* Menu Icon for Sidebar Toggle */}
        <IconButton
          edge="start"
          color="inherit"
          aria-label="menu"
          onClick={toggleSidebar}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        {/* Logo and Title */}
        <Box
          display="flex"
          alignItems="center"
          sx={{
            flexGrow: 1,
            flexDirection: isMobile ? 'column' : 'row', // Stack logo and text on mobile
            textAlign: isMobile ? 'center' : 'left',
          }}
        >
          <img
            src="/assets/thapar_logo.png"
            alt="TIET Logo"
            style={{
              height: isMobile ? '30px' : '40px', // Adjust logo size for mobile
              marginRight: isMobile ? '0' : '10px',
              marginBottom: isMobile ? '5px' : '0',
            }}
          />
          <Typography
            variant={isMobile ? 'body1' : 'h6'} // Smaller text on mobile
            component="div"
          >
            TIET Vehicle Surveillance Dashboard
          </Typography>
        </Box>

        {/* Logout Button */}
        <Button color="inherit" sx={{ fontSize: isMobile ? '12px' : 'inherit' }}>
          Logout
        </Button>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
