// controller/ws4.js

const WebSocket = require("ws");
const { spawn } = require("child_process");
const config = require("../config");
const mediasoup = require("mediasoup");
const { v4: uuidv4 } = require("uuid");
const stream = require("stream");

const pythonProcesses = {};
const pythonSockets = {};
const pipeTransports = {};
const producers = {};

let mediaSoupRouter;
let mediaSoupWorker;

// Initialize Mediasoup Worker and Router
const initializeMediasoup = async () => {
  mediaSoupWorker = await mediasoup.createWorker({
    rtcMinPort: config.mediasoup.worker.rtcMinPort,
    rtcMaxPort: config.mediasoup.worker.rtcMaxPort,
  });

  console.log(`Mediasoup Worker created with PID: ${mediaSoupWorker.pid}`);

  mediaSoupWorker.on("died", () => {
    console.error("Mediasoup Worker died");
    process.exit(1);
  });

  mediaSoupRouter = await mediaSoupWorker.createRouter({
    mediaCodecs: config.mediasoup.router.mediaCodecs,
  });
  console.log(`Mediasoup Router created: ${mediaSoupRouter.id}`);
};

// Utility function to check if a string is valid JSON
const isJsonString = (str) => {
  try {
    JSON.parse(str);
  } catch (error) {
    return false;
  }
  return true;
};

// Function to send responses to the client
const sendResponse = (ws, type, data) => {
  console.log(`Sending response of type: ${type}`, data);
  ws.send(
    JSON.stringify({
      type,
      data,
    })
  );
};

// Function to get port based on feedId
const getPortByFeedId = (feedId) => {
  const feedNumber = parseInt(feedId.replace("feed", ""), 10);
  return 3000 + feedNumber; // feed1 -> 3001, feed2 -> 3002, etc.
};

// Function to handle incoming video frames from Python
const handlePythonFrames = async (frameData, feedId, websocketServer) => {
  try {
    const buffer = Buffer.from(frameData, "base64"); // Decode the base64 frame
    const message = {
      type: "videoFrame",
      data: {
        feedId,
        frame: `data:image/jpeg;base64,${frameData}`, // Add `data:image/jpeg;base64` prefix
      },
    };

    // Broadcast the frame to all connected frontend clients
    websocketServer.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(message));
      }
    });
  } catch (error) {
    console.error(`Error handling frames for ${feedId}:`, error);
  }
};

// Function to create a Pipe Transport for a specific feed
const createPipeTransport = async (feedId) => {
  try {
    const transport = await mediaSoupRouter.createPipeTransport({
      listenIp: "127.0.0.1",
      enableSctp: false,
      enableRtpHeaderExtensions: false,
      enableUdp: false,
      enableTcp: true, // Using TCP for Pipe Transport
    });

    // Store the transport
    pipeTransports[feedId] = transport;

    // Handle transport events if needed
    transport.on("close", () => {
      console.log(`Pipe Transport closed for ${feedId}`);
      delete pipeTransports[feedId];
    });

    return transport;
  } catch (error) {
    console.error(`Error creating Pipe Transport for ${feedId}:`, error);
    throw error;
  }
};

// Function to create a Producer from the Pipe Transport
const createProducerFromPipe = async (feedId) => {
  try {
    const transport = pipeTransports[feedId];
    if (!transport) {
      console.error(`No Pipe Transport found for ${feedId}`);
      return;
    }

    const producer = await transport.produce({
      kind: "video",
      rtpParameters: mediaSoupRouter.rtpCapabilities,
    });

    producers[feedId] = producer;

    console.log(`Producer created for ${feedId}: ${producer.id}`);

    producer.on("transportclose", () => {
      console.log(`Producer transport closed for ${feedId}`);
      producer.close();
      delete producers[feedId];
    });

    producer.on("close", () => {
      console.log(`Producer closed for ${feedId}`);
      delete producers[feedId];
    });
  } catch (error) {
    console.error(`Error creating producer for ${feedId}:`, error);
  }
};

// Function to handle starting a feed
const handleStartFeed = (ws, data, websocketServer) => {
  const { feedId } = data; // Ensure feedId is like 'feed1', 'feed2', etc.
  if (pythonProcesses[feedId]) {
    sendResponse(ws, "error", { message: "Feed already running" });
    return;
  }

  // Spawn feed.py with the given feedId
  const pythonProcess = spawn("python", ["feed.py", feedId]);

  pythonProcesses[feedId] = pythonProcess;

  pythonProcess.stdout.on("data", (data) => {
    console.log(`Feed ${feedId}: ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`Feed ${feedId} Error: ${data}`);
  });

  pythonProcess.on("close", (code) => {
    console.log(`Feed ${feedId} exited with code ${code}`);
    delete pythonProcesses[feedId];
    if (pythonSockets[feedId]) {
      pythonSockets[feedId].close();
      delete pythonSockets[feedId];
    }
  });

  sendResponse(ws, "feedStarted", { feedId });

  // After starting the feed, connect to its WebSocket
  const port = getPortByFeedId(feedId);
  const feedWebSocketUrl = `ws://127.0.0.1:${port}/${feedId}`;

  const connectToFeed = () => {
    const socket = new WebSocket(feedWebSocketUrl);

    socket.on("open", () => {
      console.log(`Connected to Python feed ${feedId} on port ${port}`);
    });

    socket.on("message", (message) => {
      try {
        const data = JSON.parse(message);
        if (data.type === "videoFrame") {
          handlePythonFrames(data.data.frame, feedId, websocketServer);
        }
      } catch (error) {
        console.error(`Error parsing message from feed ${feedId}:`, error);
      }
    });

    socket.on("error", (error) => {
      console.error(`WebSocket error for feed ${feedId}:`, error);
    });

    socket.on("close", () => {
      console.log(`WebSocket connection to feed ${feedId} closed`);
      delete pythonSockets[feedId];
    });

    pythonSockets[feedId] = socket;
  };

  // Delay the connection slightly to ensure feed.py is up
  setTimeout(connectToFeed, 1000);
};

const stopFeed = async (ws, data) => {
  const { feedId } = data;

  if (!producers[feedId]) {
    sendResponse(ws, "error", {
      message: `No active feed for feedId: ${feedId}`,
    });
    return;
  }

  try {
    // Close the producer
    producers[feedId].close();
    delete producers[feedId];

    // Close pipe transport
    if (pipeTransports[feedId]) {
      pipeTransports[feedId].close();
      delete pipeTransports[feedId];
    }

    // Stop the Python process
    if (pythonProcesses[feedId]) {
      pythonProcesses[feedId].kill();
      delete pythonProcesses[feedId];
    }

    sendResponse(ws, "feedStopped", { feedId });
  } catch (error) {
    console.error(`Error stopping feed ${feedId}:`, error);
    sendResponse(ws, "error", { message: error.message });
  }
};

// WebSocket Connection Handler
const WebSocketConnection = async (websocketServer) => {
  try {
    await initializeMediasoup();

    websocketServer.on("connection", async (ws) => {
      console.log("Client connected");

      ws.on("message", async (message) => {
        console.log("Received message:", message);
        if (!isJsonString(message)) {
          console.error("Invalid JSON");
          return;
        }

        const event = JSON.parse(message);

        switch (event.type) {
          case "startFeed":
            handleStartFeed(ws, event.data, websocketServer);
            break;
          case "getRouterRtpCapabilities":
            sendResponse(
              ws,
              "routerRtpCapabilities",
              mediaSoupRouter.rtpCapabilities
            );
            break;
          case "stopFeed":
            stopFeed(ws, event.data);
            break;
          case "createConsumerTransport":
            // Implement createConsumerTransport logic here
            break;
          case "connectConsumerTransport":
            // Implement connectConsumerTransport logic here
            break;
          case "consume":
            // Implement consume logic here
            break;
          // ... handle other message types ...
          default:
            console.error("Unknown message type:", event.type);
            break;
        }
      });

      ws.on("close", () => {
        console.log("Client disconnected");
        // Clean up resources if necessary
      });
    });

    console.log("WebSocket server is ready");
  } catch (error) {
    console.error("WebSocketConnection error:", error);
  }
};

module.exports = WebSocketConnection;
