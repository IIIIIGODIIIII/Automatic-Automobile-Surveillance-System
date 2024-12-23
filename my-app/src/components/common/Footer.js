// src/components/Footer.js
import React from 'react';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="system-status">System Status: Operational</div>
      <div className="last-update-time">Last Updated: {new Date().toLocaleString()}</div>
      <div className="contact-info">Contact: support@example.com</div>
    </footer>
  );
};

export default Footer;
