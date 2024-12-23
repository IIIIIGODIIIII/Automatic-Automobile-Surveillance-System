import React from "react";
import { Card, CardContent, Typography, Box } from "@mui/material";

const Alert = ({ vehicleNumber, speed, location, timestamp }) => {
  return (
    <Card sx={{ borderRadius: '12px', boxShadow: 3 }}>
      <CardContent>
        <Box display="flex" flexDirection="column" gap={1}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            Vehicle: {vehicleNumber}
          </Typography>
          <Typography variant="body1" color="error">
            Speed: {speed} km/h
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Location: {location}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Time: {timestamp}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default Alert;
