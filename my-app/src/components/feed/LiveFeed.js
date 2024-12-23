import React from 'react';
import { Card, CardContent, Typography, Button } from '@mui/material';

const LiveFeed = ({ feedId, location, isOverspeeding, videoSrc, publish }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6">{location}</Typography>
        {isOverspeeding && (
          <Typography variant="body1" color="error">
            Overspeeding!
          </Typography>
        )}
        {videoSrc ? (
          <img src={videoSrc} alt={`Feed for ${feedId}`} width="100%" />
        ) : (
          <Typography variant="body2">No video available</Typography>
        )}
        <Button variant="contained" color="primary" onClick={publish} sx={{ mt: 2 }}>
          Publish
        </Button>
      </CardContent>
    </Card>
  );
};

export default LiveFeed;