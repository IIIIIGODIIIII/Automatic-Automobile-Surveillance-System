// index.js
const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const dotenv = require('dotenv')
const connectToMongo = require('./db');
const cors = require('cors');
const vechileRouter = require('./routes/vechiles');
const alertRouter = require('./routes/alert');
const trafficRouter = require('./routes/traffic');
const WebSocketConnection = require('./controller/ws3');
const config = require('./config');
// const mediasoupHandler = require('./controller/ws5');

dotenv.config();
connectToMongo();

const port = process.env.PORT || 8000;
const app = express();
const server = http.createServer(app);
// const wss = new WebSocket.Server({ server,path: '/ws' });

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files (if any)
app.use(express.static(path.join(__dirname, 'public')));
app.use(cors(
    {
        origin: 'http://localhost:3000',
        credentials: true
    }
));
// Serve Homepage
app.get('/', (req, res) => {
    res.send('WebSocket Server is Running');
});

// Routes
app.use('/vechiles', vechileRouter.router);
app.use('/alerts', alertRouter.router);
app.use('/traffic', trafficRouter.router);

// Initialize Mediasoup and handle WebSocket connections
const wss = new WebSocket.Server({ noServer: true });
WebSocketConnection(wss);

server.on('upgrade', (request, socket, head) => {
    const { url } = request;
    if (url.startsWith('/ws')) {
        wss.handleUpgrade(request, socket, head, (ws) => {
            wss.emit('connection', ws, request);
        });
    } else {
        socket.destroy();
    }
});

server.listen(port, () => {
    console.log(`Server listening on http://localhost:${port}`);
});