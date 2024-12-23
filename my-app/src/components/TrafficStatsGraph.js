import React, { useRef, useEffect } from 'react';
import { Line, Pie } from 'react-chartjs-2';
import 'chart.js/auto';
import './TrafficStatsGraph.css';

const TrafficStatsGraph = () => {
  const chartRef = useRef(null);

  const data = {
    labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    datasets: [
      {
        label: 'Traffic Stats',
        data: [65, 59, 80, 81, 56, 55, 40], // Example data
        fill: false,
        backgroundColor: 'rgba(75,192,192,0.2)',
        borderColor: 'rgba(75,192,192,1)',
      },
    ],
  };

  const options = {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  const pieData = {
    labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    datasets: [
      {
        label: 'Overspeeding Incidents',
        data: [12, 19, 3, 5, 2, 3, 7], // Example data
        backgroundColor: [
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
          'rgba(255, 206, 86, 0.2)',
          'rgba(75, 192, 192, 0.2)',
          'rgba(153, 102, 255, 0.2)',
          'rgba(255, 159, 64, 0.2)',
          'rgba(199, 199, 199, 0.2)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(199, 199, 199, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  useEffect(() => {
    const chartInstance = chartRef.current;

    return () => {
      if (chartInstance) {
        chartInstance.destroy();
      }
    };
  }, []);

  return (
    <div className="traffic-stats-graph-container">
      <div className="line-chart-container">
        <Line ref={chartRef} data={data} options={options} />
      </div>
      <div className="pie-chart-container">
        <Pie data={pieData} options={{ maintainAspectRatio: false }} />
      </div>
    </div>
  );
};

export default TrafficStatsGraph;