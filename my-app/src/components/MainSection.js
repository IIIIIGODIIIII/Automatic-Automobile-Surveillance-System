// src/components/MainSection.js
import React, { useState } from 'react';
import './MainSection.css';
import TrafficStatsGraph from './TrafficStatsGraph';
import OverspeedingReports from './OverspeedingReports';

const LiveFeed = ({ location, isOverspeeding }) => {
  return (
    <div className="live-feed">
      <video className="feed-video" controls>
        <source src="your-video-source.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      <div className="feed-info">
        <span className="location">{location}</span>
        <span className={`alert-indicator ${isOverspeeding ? 'alert-red blinking' : 'alert-green'}`}></span>
      </div>
    </div>
  );
};

const Alert = ({ vehicleNumber, speed, location, timestamp }) => {
  return (
    <div className="alert">
      <div className="alert-info">
        <span className="alert-vehicle">Vehicle: {vehicleNumber}</span>
        <span className="alert-speed">Speed: {speed} km/h</span>
        <span className="alert-location">Location: {location}</span>
        <span className="alert-timestamp">Time: {timestamp}</span>
      </div>
    </div>
  );
};

const RegisteredVehicles = () => {
  const [vehicles, setVehicles] = useState([
    { number: 'AB123CD', owner: 'John Doe', model: 'Toyota Camry', year: 2020 },
    { number: 'EF456GH', owner: 'Jane Smith', model: 'Honda Accord', year: 2019 },
    { number: 'IJ789KL', owner: 'Alice Johnson', model: 'Ford Focus', year: 2018 },
    { number: 'MN012OP', owner: 'Bob Brown', model: 'Tesla Model 3', year: 2021 },
  ]);

  const [newVehicle, setNewVehicle] = useState({
    number: '',
    owner: '',
    model: '',
    year: ''
  });

  const [showForm, setShowForm] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewVehicle({ ...newVehicle, [name]: value });
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    setVehicles([...vehicles, newVehicle]);
    setNewVehicle({ number: '', owner: '', model: '', year: '' });
    setShowForm(false);
  };

  return (
    <div className="registered-vehicles-section">
      <table className="vehicles-table">
        <thead>
          <tr>
            <th>Vehicle Number</th>
            <th>Owner</th>
            <th>Model</th>
            <th>Year</th>
          </tr>
        </thead>
        <tbody>
          {vehicles.map((vehicle, index) => (
            <tr key={index}>
              <td>{vehicle.number}</td>
              <td>{vehicle.owner}</td>
              <td>{vehicle.model}</td>
              <td>{vehicle.year}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {showForm && (
        <form className="register-form" onSubmit={handleFormSubmit}>
          <input
            type="text"
            name="number"
            placeholder="Vehicle Number"
            value={newVehicle.number}
            onChange={handleInputChange}
            required
          />
          <input
            type="text"
            name="owner"
            placeholder="Owner"
            value={newVehicle.owner}
            onChange={handleInputChange}
            required
          />
          <input
            type="text"
            name="model"
            placeholder="Model"
            value={newVehicle.model}
            onChange={handleInputChange}
            required
          />
          <input
            type="number"
            name="year"
            placeholder="Year"
            value={newVehicle.year}
            onChange={handleInputChange}
            required
          />
          <button type="submit" className="submit-button">Add Vehicle</button>
        </form>
      )}

      <div className="register-button-container">
        <button
          className="register-new-vehicle-button"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : 'Register New Vehicle'}
        </button>
      </div>
    </div>
  );
};

const Dashboard = () => {
  return (
    <div className="dashboard">
      <div className="dashboard-content">
        <div className="text-content">
          <h1>Vehicle Surveillance System</h1>
          <p className="subtitle">For Enhanced Safety at Thapar University</p>
          <p>
            The Vehicle Surveillance System provides comprehensive monitoring and
            analysis of vehicular movements. Here, you'll find insights into live feeds,
            alerts for overspeeding, registered vehicles, traffic statistics, and more.
          </p>
        </div>
        <img src="/assets/thapar_logo.png" alt="Thapar University" className="thaparLogo" />
      </div>
    </div>
  );
};

const MainSection = ({ activeSection }) => {
  const feeds = [
    { location: 'Location 1', isOverspeeding: false },
    { location: 'Location 2', isOverspeeding: true },
    { location: 'Location 3', isOverspeeding: false },
    { location: 'Location 4', isOverspeeding: true },
    { location: 'Location 5', isOverspeeding: false },
    { location: 'Location 6', isOverspeeding: true },
    { location: 'Location 7', isOverspeeding: false },
    { location: 'Location 8', isOverspeeding: true },
  ];

  const alerts = [
    { vehicleNumber: 'AB123CD', speed: 80, location: 'Area 1', timestamp: '2024-08-23 10:00' },
    { vehicleNumber: 'EF456GH', speed: 95, location: 'Area 2', timestamp: '2024-08-23 10:05' },
    { vehicleNumber: 'IJ789KL', speed: 110, location: 'Area 3', timestamp: '2024-08-23 10:10' },
    { vehicleNumber: 'MN012OP', speed: 120, location: 'Area 4', timestamp: '2024-08-23 10:15' },
    { vehicleNumber: 'QR345ST', speed: 70, location: 'Area 5', timestamp: '2024-08-23 10:20' },
  ];

  return (
    <main className="main-section">
      {activeSection === 'dashboard' && <Dashboard />}
      {activeSection === 'liveFeeds' && (
        <div className="live-feeds-grid">
          {feeds.map((feed, index) => (
            <LiveFeed
              key={index}
              location={feed.location}
              isOverspeeding={feed.isOverspeeding}
            />
          ))}
        </div>
      )}
      {activeSection === 'alerts' && (
        <div className="alerts-list">
          {alerts.map((alert, index) => (
            <Alert
              key={index}
              vehicleNumber={alert.vehicleNumber}
              speed={alert.speed}
              location={alert.location}
              timestamp={alert.timestamp}
            />
          ))}
        </div>
      )}
      {activeSection === 'registeredVehicles' && <RegisteredVehicles />}
      {activeSection === 'trafficStats' && <div className="traffic-stats-graph">Traffic Stats Graph</div>}
      {activeSection === 'overspeedingReports' && <OverspeedingReports />}
      {activeSection === 'settings' && <div>Settings</div>}
    </main>
  );
};

export default MainSection;
