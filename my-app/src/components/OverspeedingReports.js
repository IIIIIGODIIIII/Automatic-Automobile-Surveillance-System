// src/components/OverspeedingReports.js
import React from 'react';
import './OverspeedingReports.css';

const overspeedingReports = [
  { id: 1, vehicleNumber: 'AB123CD', speed: 120, location: 'Area 1', coordinates: { x: 150, y: 200 } },
  { id: 2, vehicleNumber: 'EF456GH', speed: 130, location: 'Area 2', coordinates: { x: 300, y: 250 } },
  { id: 3, vehicleNumber: 'IJ789KL', speed: 140, location: 'Area 3', coordinates: { x: 450, y: 150 } },
  { id: 4, vehicleNumber: 'MN012OP', speed: 150, location: 'Area 4', coordinates: { x: 600, y: 300 } },
];

const OverspeedingReports = () => {
  return (
    <div className="overspeeding-reports-container">
      <h2>Overspeeding Reports</h2>
      <div className="map-container">
        <div className="map">
          {overspeedingReports.map((report) => (
            <div
              key={report.id}
              className="marker"
              style={{ left: `${report.coordinates.x}px`, top: `${report.coordinates.y}px` }}
            >
              <div className="tooltip">
                <div><strong>Vehicle:</strong> {report.vehicleNumber}</div>
                <div><strong>Speed:</strong> {report.speed} km/h</div>
                <div><strong>Location:</strong> {report.location}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OverspeedingReports;
