// src/App.js
import React, { useState } from 'react';
import './App.css';
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import HomePage from './pages/HomePage';
import LiveFeedsPage from './pages/LiveFeedsPage';
import RegisteredVehiclesPage from './pages/RegisteredVechilesPage';
import AlertPage from './pages/AlertPage';
import OverSpeedingReportsPage from './pages/OverSpeedingReportsPage';
import TrafficStatsPage from './pages/TrafficStatsPage';

const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/livefeeds",
    element: <LiveFeedsPage/>,
  },
  {
    path: '/registeredVehicles',
    element: <RegisteredVehiclesPage />,
  },
  {
    path: '/alerts',
    element: <AlertPage />,
  },
  {
    path: '/overspeedingReports',
    element: <OverSpeedingReportsPage />,
  },
  {
    path: '/trafficStats',
    element: <TrafficStatsPage />,
  }
]);


const App = () => {
  return (
    <div className="app">
      <RouterProvider router={router} />
    </div>
  );
};

export default App;
