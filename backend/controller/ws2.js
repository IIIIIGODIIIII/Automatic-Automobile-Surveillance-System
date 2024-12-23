// ws2.js
const WebSocket = require('ws');
const { createWorker } = require('./worker'); // Ensure correct relative path
const { createWebRtcTransport } = require('./createWebRtcTransport'); // Ensure correct relative path
const { spawn } = require('child_process');

// Configuration
const config = require('../config'); // Ensure correct relative path

// Map to manage feeds: feedId => { producer, ffmpegProcess, feedProcess }
const feeds = {};

// mediasoup router
let mediaSoupRouter;

// Utility function to validate JSON strings
const isJsonString = (str) => {
    try {
        JSON.parse(str);
    } catch (error) {
        return false;
    }
    return true;
};

// Function to send responses to a WebSocket client
const sendResponse = (ws, type, data) => {
    ws.send(JSON.stringify({
        type,
        data,
    }));
};

// Function to broadcast messages to all connected frontend clients
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

// Function to create a PipeTransport for RTP streams
const createRtpPipeTransport = async () => {
    try {
        const pipeTransport = await mediaSoupRouter.createPipeTransport({
            listenIp: '127.0.0.1', // Localhost for RTP
            enableSctp: false, // Disable SCTP if not needed
            enableUdp: false, // Disable UDP for PipeTransport
            enableTcp: false, // Disable TCP for PipeTransport
        });

        pipeTransport.on('dtlsstatechange', (dtlsState) => {
            if (dtlsState === 'closed') {
                pipeTransport.close();
            }
        });

        pipeTransport.on('close', () => {
            console.log('RTP PipeTransport closed');
        });

        console.log('RTP PipeTransport created');

        return pipeTransport;
    } catch (error) {
        console.error('Error creating PipeTransport:', error);
        throw error;
    }
};

// Function to initialize and handle RTP Transport and Producer
const initializeRtpTransport = async () => {
    try {
        const rtpTransport = await createRtpPipeTransport();

        // You can store the RTP transport if needed
        // For example: global.rtpTransport = rtpTransport;

        // No specific producer creation here as FFmpeg will send RTP to this transport's port

        console.log('RTP Transport is ready to receive streams from FFmpeg');
    } catch (error) {
        console.error('Failed to initialize RTP Transport:', error);
    }
};

// Handler to create a WebRTC transport for producers/consumers
const handleCreateTransport = async (ws, transportType) => {
    try {
        const { transport, params } = await createWebRtcTransport(mediaSoupRouter);
        if (transportType === 'producer') {
            ws.producerTransport = transport;
            sendResponse(ws, 'producerTransportCreated', params);
        } else if (transportType === 'consumer') {
            ws.consumerTransport = transport;
            sendResponse(ws, 'consumerTransportCreated', params);
        }
    } catch (error) {
        console.error(`Error creating ${transportType} transport:`, error);
        sendResponse(ws, 'error', { message: error.message });
    }
};

// Handler to connect the transport
const handleConnectTransport = async (ws, transportType, dtlsParameters) => {
    try {
        if (transportType === 'producer') {
            if (!ws.producerTransport) throw new Error('Producer transport not found');
            await ws.producerTransport.connect({ dtlsParameters });
            sendResponse(ws, 'producerConnected', 'Producer transport connected');
        } else if (transportType === 'consumer') {
            if (!ws.consumerTransport) throw new Error('Consumer transport not found');
            await ws.consumerTransport.connect({ dtlsParameters });
            sendResponse(ws, 'consumerTransportConnected', 'Consumer transport connected');
        }
    } catch (error) {
        console.error(`Error connecting ${transportType} transport:`, error);
        sendResponse(ws, 'error', { message: error.message });
    }
};

// Handler to produce a stream from the producer transport
const handleProduce = async (event, ws, websocketVideoFeed) => {
    try {
        const { kind, rtpParameters, feedId } = event;

        if (!feedId) {
            throw new Error('feedId is required to produce');
        }

        if (!ws.producerTransport) {
            throw new Error('Producer transport not initialized');
        }

        // Create a producer for the specified feed
        const producer = await ws.producerTransport.produce({ kind, rtpParameters });
        feeds[feedId] = { producer, ffmpegProcess: null, feedProcess: null };

        sendResponse(ws, 'producerCreated', { id: producer.id });

        // Start the corresponding feed.py and FFmpeg processes if not already running
        if (!feeds[feedId].feedProcess && !feeds[feedId].ffmpegProcess) {
            startFeedProcess(feedId, websocketVideoFeed);
        }

        // Inform all frontend clients about the new producer
        broadcast(websocketVideoFeed, 'newProducer', { feedId, producerId: producer.id });

    } catch (error) {
        console.error('Error in handleProduce:', error);
        sendResponse(ws, 'error', { message: error.message });
    }
};

// Function to start the feed.py and FFmpeg processes for a given feedId
const startFeedProcess = (feedId, websocketVideoFeed) => {
    // Start the feed.py script as a child process
    const feedProcess = spawn('python', ['feed.py', feedId, 'ws://localhost:3000/ws/video']);

    feedProcess.stdout.on('data', (data) => {
        console.log(`feed.py [${feedId}] stdout: ${data}`);
    });

    feedProcess.stderr.on('data', (data) => {
        console.error(`feed.py [${feedId}] stderr: ${data}`);
    });

    feedProcess.on('close', (code) => {
        console.log(`feed.py [${feedId}] process exited with code ${code}`);
        stopFeed(feedId);
    });

    feeds[feedId].feedProcess = feedProcess;

    // Start FFmpeg to encode and send frames to mediasoup
    const ffmpeg = spawn('ffmpeg', [
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-i', '-', // Input from stdin
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-tune', 'zerolatency',
        '-f', 'rtp',
        'rtp://127.0.0.1:5004' // RTP destination (should match RTP PipeTransport)
    ]);

    ffmpeg.stderr.on('data', (data) => {
        console.error(`FFmpeg [${feedId}] stderr: ${data}`);
    });

    ffmpeg.on('close', (code) => {
        console.log(`FFmpeg [${feedId}] process exited with code ${code}`);
        stopFeed(feedId);
    });

    feeds[feedId].ffmpegProcess = ffmpeg;
};

// Handler to consume a stream from the consumer transport
const handleConsume = async (event, ws) => {
    try {
        const { consumerTransportId, producerId, rtpCapabilities } = event;

        // Validate RTP capabilities
        if (!mediaSoupRouter.canConsume({ producerId, rtpCapabilities })) {
            throw new Error('Cannot consume');
        }

        if (!ws.consumerTransport) {
            throw new Error('Consumer transport not initialized');
        }

        const consumer = await ws.consumerTransport.consume({
            producerId,
            rtpCapabilities,
            paused: true,
        });

        consumer.on('transportclose', () => {
            console.log('Consumer transport closed');
            consumer.close();
        });

        consumer.on('producerclose', () => {
            console.log('Producer closed');
            consumer.close();
        });

        sendResponse(ws, 'consumed', {
            id: consumer.id,
            producerId: consumer.producerId,
            kind: consumer.kind,
            rtpParameters: consumer.rtpParameters,
        });
    } catch (error) {
        console.error('Error in handleConsume:', error);
        sendResponse(ws, 'error', { message: error.message });
    }
};

// Handler to subscribe to a specific feed
const handleSubscribeFeed = async (event, ws) => {
    const { feedId } = event;

    if (!feedId || !feeds[feedId]) {
        sendResponse(ws, 'error', { message: 'Invalid feedId for subscription' });
        return;
    }

    // Inform the frontend to subscribe to the specified producer
    sendResponse(ws, 'newProducer', { feedId, producerId: feeds[feedId].producer.id });
};

// Handler to stop a specific feed
const handleStopFeed = async (event, ws) => {
    const { feedId } = event;

    if (!feedId || !feeds[feedId]) {
        sendResponse(ws, 'error', { message: 'Invalid feedId to stop' });
        return;
    }

    stopFeed(feedId);

    sendResponse(ws, 'feedStopped', { feedId });
};

// Function to stop a feed by feedId
const stopFeed = (feedId) => {
    const feed = feeds[feedId];
    if (feed) {
        // Close the producer
        if (feed.producer) {
            feed.producer.close();
        }

        // Terminate the feed.py process
        if (feed.feedProcess) {
            feed.feedProcess.kill();
        }

        // Terminate the FFmpeg process
        if (feed.ffmpegProcess) {
            feed.ffmpegProcess.kill();
        }

        // Remove the feed from the map
        delete feeds[feedId];
        console.log(`Feed ${feedId} has been stopped and cleaned up`);
    }
};

// Handler for frontend WebSocket connections
const handleFrontendConnection = async (ws, websocketVideoFeed) => {
    ws.on('message', async (message) => {
        if (!isJsonString(message)) {
            console.error('Invalid JSON from frontend');
            return;
        }

        const event = JSON.parse(message);
        switch (event.type) {
            case 'getFeeds':
                // Send the list of available feeds
                sendResponse(ws, 'feeds', Object.keys(feeds));
                break;
            case 'createProducerTransport':
                await handleCreateTransport(ws, 'producer');
                break;
            case 'connectProducerTransport':
                await handleConnectTransport(ws, 'producer', event.dtlsParameters);
                break;
            case 'produce':
                await handleProduce(event, ws, websocketVideoFeed);
                break;
            case 'createConsumerTransport':
                await handleCreateTransport(ws, 'consumer');
                break;
            case 'connectConsumerTransport':
                await handleConnectTransport(ws, 'consumer', event.dtlsParameters);
                break;
            case 'consume':
                await handleConsume(event, ws);
                break;
            case 'subscribeFeed':
                await handleSubscribeFeed(event, ws);
                break;
            case 'stopFeed':
                await handleStopFeed(event, ws);
                break;
            default:
                console.error('Unknown message type from frontend:', event.type);
                sendResponse(ws, 'error', { message: 'Unknown message type' });
                break;
        }
    });

    ws.on('close', (code,reason) => {
        console.log(`Frontend client disconnected: code =${code}, reason = ${reason}`);
        // Optional: Handle cleanup if needed
    });
};

// Handler for video feed WebSocket connections (from feed.py)
const handleVideoFeedConnection = (ws) => {
    let currentFeedId = null;

    ws.on('message', async (message) => {
        if (!isJsonString(message)) {
            console.error('Invalid JSON from feed.py');
            return;
        }

        const event = JSON.parse(message);
        const { feedId, frame } = event;

        if (!feedId || !frame) {
            console.error('Invalid frame data from feed.py');
            return;
        }

        if (!feeds[feedId] || !feeds[feedId].producer) {
            console.error(`No producer found for feedId: ${feedId}`);
            return;
        }

        // Convert base64 frame to binary Buffer
        const buffer = Buffer.from(frame, 'base64');

        // Write the frame buffer to FFmpeg's stdin
        const ffmpegProcess = feeds[feedId].ffmpegProcess;
        if (ffmpegProcess && ffmpegProcess.stdin.writable) {
            ffmpegProcess.stdin.write(buffer);
        } else {
            console.error(`FFmpeg process for feedId ${feedId} is not writable`);
        }
    });

    ws.on('close', () => {
        console.log('feed.py client disconnected');
        if (currentFeedId && feeds[currentFeedId]) {
            // Handle feed cleanup
            stopFeed(currentFeedId);
        }
    });
};

// Main WebSocket connection handler
const WebSocketConnection = async (websocketFrontend, websocketVideoFeed) => {
    try {
        websocketFrontend.options.perMessageDeflate = false;
        websocketVideoFeed.options.perMessageDeflate = false;

        // Initialize mediasoup worker and router
        mediaSoupRouter = await createWorker();
        console.log('mediasoup router created');

        // Initialize RTP PipeTransport
        await initializeRtpTransport();
    } catch (error) {
        console.error('Failed to initialize mediasoup:', error);
        process.exit(1);
    }

    // Handle frontend client connections
    websocketFrontend.on('connection', (ws) => {
        console.log('Frontend client connected');
        handleFrontendConnection(ws, websocketVideoFeed);
    });

    // Handle video feed connections from feed.py
    websocketVideoFeed.on('connection', (ws) => {
        console.log('Video Feed client connected');
        handleVideoFeedConnection(ws);
    });
};

module.exports = WebSocketConnection;