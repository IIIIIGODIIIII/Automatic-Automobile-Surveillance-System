// ws.js
const WebSocket = require('ws');
const { createWorker } = require('./worker');
const { createWebRtcTransport } = require('./createWebRtcTransport');

let mediaSoupRouter;
let producerTransport;
let producer;
let consumerTransport;
let consumer;

const isJsonString = (str) => {
    try {
        JSON.parse(str);
    } catch (error) {
        return false;
    }
    return true;
};

const handleGetRouterRtpCapabilities = async (ws, event) => {
    sendResponse(ws, 'routerRtpCapabilities', mediaSoupRouter.rtpCapabilities);
};

const onCreateProducerTransport = async (ws, event, websocket) => {
    try {
        const { transport, params } = await createWebRtcTransport(mediaSoupRouter);
        producerTransport = transport;
        sendResponse(ws, 'producerTransportCreated', params);

    } catch (error) {
        console.error('Error creating producer transport:', error);
        sendResponse(ws, "error", { message: error.message });
    }
};

const onConnectProducerTransport = async (ws, event) => {
    try {
        await producerTransport.connect({ dtlsParameters: event.dtlsParameters });
        sendResponse(ws, 'producerConnected', 'producer connected');
    } catch (error) {
        console.error('Error connecting producer transport:', error);
        sendResponse(ws, "error", { message: error.message });
    }
};

const onProduce = async (event, ws, websocket) => {
    try {
        const { kind, rtpParameters } = event;
        producer = await producerTransport.produce({ kind, rtpParameters });
        sendResponse(ws, 'producerCreated', { id: producer.id });
        broadcast(websocket, 'newProducer', `New producer: ${producer.id}`);
    } catch (error) {
        console.error('Error producing:', error);
        sendResponse(ws, "error", { message: error.message });
    }
};

const onCreateConsumerTransport = async (event, ws, websocket) => {
    try {
        const { transport, params } = await createWebRtcTransport(mediaSoupRouter);
        consumerTransport = transport;
        sendResponse(ws, 'consumerTransportCreated', params);
    }
    catch (error) {
        console.error('Error creating consumer transport:', error);
        sendResponse(ws, 'error', { message: error.message });
    }
};

const onConnectConsumerTransport = async (event, ws) => {
    try {
        await consumerTransport.connect({ dtlsParameters: event.dtlsParameters });
        sendResponse(ws, 'consumerTransportConnected', 'consumer transport connected');
    } catch (error) {
        console.error('Error connecting consumer transport:', error);
        sendResponse(ws, "error", { message: error.message });
    }
};

const sendResponse = (ws, type, data) => {
    ws.send(JSON.stringify({
        type,
        data,
    }));
};

const broadcast = (websocketServer, type, msg) => {
    if (!websocketServer || !websocketServer.clients) {
        console.error('WebSocket server is not defined or has no clients');
        return;
    }
    
    const message = {
        type,
        data: msg
    };
    const resp = JSON.stringify(message);
    websocketServer.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(resp);
        }
    });
};

const onResume = async (ws) => {
    try {
        await consumer.resume();
        sendResponse(ws, 'resumed', 'resumed');
    } catch (error) {
        console.error('Error resuming consumer:', error);
        sendResponse(ws, 'error', { message: error.message });
    }
};

const onConsume = async (event, ws) => {
    try {
        const res = await createConsumer(producer, event.rtpCapabilities);
        if (res) {
            sendResponse(ws, 'subscribed', res);
        }
    } catch (error) {
        console.error('Error consuming:', error);
        sendResponse(ws, 'error', { message: error.message });
    }
};

const createConsumer = async (producer, rtpCapabilities) => {
    if (!mediaSoupRouter.canConsume({
        producerId: producer.id,
        rtpCapabilities,
    })) {
        console.error('Cannot consume');
        return;
    }

    try {
        consumer = await consumerTransport.consume({
            producerId: producer.id,
            rtpCapabilities,
            paused: producer.kind === 'video',
        });
    } catch (error) {
        console.error('Consume failed!', error);
        return;
    }
    return {
        producerId: producer.id,
        id: consumer.id,
        kind: consumer.kind,
        rtpParameters: consumer.rtpParameters,
        type: consumer.type,
        producerPaused: consumer.producerPaused,
    };
};

const feeds = [
    { location: "Location 1", isOverspeeding: false, videoSrc: "video1.mp4" },
    { location: "Location 2", isOverspeeding: true, videoSrc: "video2.mp4" },
    // Add more feeds as needed
];

const WebSocketConnection = async (websocket) => {
    try {
        mediaSoupRouter = await createWorker();
    } catch (error) {
        console.error('Failed to create mediasoup router:', error);
        process.exit(1);
    }

    websocket.on('connection', (ws) => {
        console.log('Client connected');

        ws.on('message', async (message) => {
            if (!isJsonString(message)) {
                console.error('Invalid JSON');
                return;
            }

            const event = JSON.parse(message);
            switch (event.type) {
                case 'getFeeds':
                    sendResponse(ws, 'feeds', feeds);
                    break;
                case 'getRouterRtpCapabilities':
                    handleGetRouterRtpCapabilities(ws, event);
                    break;
                case 'createProducerTransport':
                    onCreateProducerTransport(ws, event, websocket); // Pass 'websocket'
                    break;
                case 'connectProducerTransport':
                    onConnectProducerTransport(ws, event);
                    break;
                case 'produce':
                    onProduce(event, ws, websocket); // Pass 'websocket'
                    break;
                case 'createConsumerTransport':
                    onCreateConsumerTransport(event, ws, websocket); // Pass 'websocket'
                    break;
                case 'connectConsumerTransport':
                    onConnectConsumerTransport(event, ws);
                    break;
                case 'resume':
                    onResume(ws);
                    break;
                case 'consume':
                    onConsume(event, ws);
                    break;
                case 'videoFrame':
                    broadcast(websocket, 'videoFrame', event.data);
                    break;
                default:
                    console.error('Invalid message type:', event.type);
                    sendResponse(ws, 'error', { message: 'Invalid message type' });
                    break;
            }
        });

        ws.on('close', () => {
            console.log('Client disconnected');
            // Clean up transports and other resources if necessary
        });
    });
}

module.exports = WebSocketConnection;