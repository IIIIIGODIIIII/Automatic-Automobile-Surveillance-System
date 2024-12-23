// src/components/Alerts.js
import React, { useEffect, useState } from 'react';
import Alert from './Alert';
import { Grid2,Container } from '@mui/material';


const Alerts = () => {
  const [alerts, setAlerts] = useState(
    []
 );
 
   useEffect(() => {
     fetch('http://localhost:8000/alerts').then(response =>
       response.json().then(data => { 
          setAlerts(data);
        })
     );
   },[]);
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
      <h1>Alerts</h1>
      <Grid2 container spacing={2}>
        {alerts && alerts.map((alert, index) => (
          <Grid2 key={index} size={{xs:12}}>
            <Alert {...alert} />
          </Grid2>
        ))}
      </Grid2>
    </Container>
  );
};

export default Alerts;
