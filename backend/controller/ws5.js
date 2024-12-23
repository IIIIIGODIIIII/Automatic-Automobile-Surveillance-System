// ws5.js

const mediasoup = require("mediasoup");
const config = require("../config");
const url = require("url");
const { spawn } = require("child_process");
const { RTCPeerConnection, RTCSessionDescription } = require("wrtc"); // Add wrtc for SDP handling

let worker;
let router;
const peers = {}; // Tracks producers (e.g., feed1 from Python client)
const consumers = {}; // Tracks consumers per consumer client (e.g., frontend connections)
const pythonProcesses = {}; // Tracks Python processes per feedId

// Initialize Mediasoup Worker and Router
const initMediasoup = async () => {
  try {
    worker = await mediasoup.createWorker({
      rtcMinPort: config.mediasoup.worker.rtcMinPort,
      rtcMaxPort: config.mediasoup.worker.rtcMaxPort,
      logLevel: config.mediasoup.worker.loglevel || "warn",
      logTags: config.mediasoup.worker.logtags || [],
    });

    worker.on("died", () => {
      console.error("Mediasoup worker died, exiting...");
      process.exit(1);
    });

    router = await worker.createRouter({
      mediaCodecs: config.mediasoup.router.mediaCodecs,
    });

    console.log("Mediasoup Router created");
  } catch (error) {
    console.error("Failed to initialize Mediasoup:", error);
    process.exit(1);
  }
};

initMediasoup();

// Export the WebSocket server handler
module.exports = (wss) => {
  wss.on("connection", async (ws, request) => {
    const query = url.parse(request.url, true).query;
    const feedId = query.feedId;
    if (!feedId) {
      ws.close();
      return;
    }

    console.log(`WebSocket connection URL: ${request.url}`);
    console.log(`Handling connection for feedId: ${feedId}`);

    // Initialize consumer tracking for consumer clients
    if (feedId.startsWith("consumer")) {
      // Assuming consumer connections have feedId like 'consumer1'
      if (!consumers[ws]) {
        consumers[ws] = { consumers: {} };
      }
    }

    ws.on("message", async (message) => {
      let data;
      try {
        data = JSON.parse(message);
      } catch (e) {
        console.error("Invalid JSON received:", message);
        return;
      }

      console.log(
        `Received message of type: ${data.type} from feedId: ${feedId}`,
        data
      );

      switch (data.type) {
        // **Producer Side Handling**

        case "publish":
          // Handle 'publish' message from frontend to start the producer
          try {
            const { feedId } = data;
            console.log(`Received publish request for feedId: ${feedId}`);
            if (pythonProcesses[feedId]) {
              console.log(
                `Python process already running for feedId: ${feedId}`
              );
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: `Feed ${feedId} is already published.`,
                })
              );
              return;
            }

            // Start the Python process for the feedId
            const pythonScriptMap = {
              feed1: "feed1.py",
              feed2: "feed2.py",
            };

            const pythonScript = pythonScriptMap[feedId];
            if (!pythonScript) {
              console.error(`No Python script mapped for feedId: ${feedId}`);
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: `No Python script mapped for feedId: ${feedId}`,
                })
              );
              return;
            }

            console.log(
              `Starting Python script: ${pythonScript} for feedId: ${feedId}`
            );

            // Spawn the Python process
            const process = spawn(
              "python",
              [pythonScript, feedId, "ws://localhost:8000/ws"],
              {
                cwd: __dirname,
                stdio: ["ignore", "pipe", "pipe"],
              }
            );

            // Store the process
            pythonProcesses[feedId] = process;

            // Handle process events
            process.stdout.on("data", (data) => {
              console.log(`[Python feed ${feedId} stdout]: ${data}`);
            });

            process.stderr.on("data", (data) => {
              console.error(`[Python feed ${feedId} stderr]: ${data}`);
            });

            process.on("close", (code) => {
              console.log(`Python feed ${feedId} exited with code ${code}`);
              delete pythonProcesses[feedId];
              // Optionally notify frontend of process termination
            });

            ws.send(JSON.stringify({ type: "publishStarted", feedId }));
            console.log(`Python script started for feedId: ${feedId}`);
          } catch (error) {
            console.error(
              `Error handling publish for feedId ${feedId}:`,
              error
            );
            ws.send(
              JSON.stringify({
                type: "error",
                message: "Failed to start publish.",
              })
            );
          }
          break;

        case "offer":
          // Handle producer offer from Python client
          try {
            const producerFeedId = feedId; // 'feed1', 'feed2', etc.
            console.log(
              `Handling offer for producer feedId: ${producerFeedId}`
            );

            const offer = data.sdp;
            const offerType = data.type_desc;

            // Create a WebRTC RTCPeerConnection to handle the offer
            const pc = new RTCPeerConnection({
              iceServers: config.mediasoup.iceServers || [],
            });

            // Add the router's RTP capabilities if needed
            // Not directly applicable here, usually handled in Mediasoup

            // Handle ICE candidates from the server side
            const iceCandidates = [];

            pc.onicecandidate = ({ candidate }) => {
              if (candidate) {
                ws.send(
                  JSON.stringify({
                    type: "candidate",
                    candidate: {
                        sdpMid: candidate.sdpMid,
                        sdpMLineIndex: candidate.sdpMLineIndex,
                        candidate: candidate.candidate
                    },
                    feedId: producerFeedId
                })
                );
                console.log(`Sent ICE candidate for feedId: ${producerFeedId}`);
              }
            };

            // Set remote description with the offer from producer
            await pc.setRemoteDescription(
              new RTCSessionDescription({ type: offerType, sdp: offer })
            );
            console.log(`Set remote description for feedId: ${producerFeedId}`);

            // Create an answer
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            console.log(
              `Created and set local answer for feedId: ${producerFeedId}`
            );

            // Send the answer back to the producer
            ws.send(
              JSON.stringify({
                type: "answer",
                sdp: pc.localDescription.sdp,
                type_desc: pc.localDescription.type,
                feedId: producerFeedId,
              })
            );
            console.log(`Sent answer for feedId: ${producerFeedId}`);

            // After setting up the connection, create a transport in Mediasoup
            const transport = await router.createWebRtcTransport(
              config.mediasoup.webRtcTransport
            );

            peers[producerFeedId] = { transport, pc };

            // Send transport parameters to the producer
            ws.send(
              JSON.stringify({
                type: "producerTransportCreated",
                data: {
                  id: transport.id,
                  iceParameters: transport.iceParameters,
                  iceCandidates: transport.iceCandidates,
                  dtlsParameters: transport.dtlsParameters,
                },
              })
            );
            console.log(
              `Created transport for producer feedId: ${producerFeedId}`
            );
          } catch (error) {
            console.error(
              `Error handling offer from producer feedId ${feedId}:`,
              error
            );
            ws.send(
              JSON.stringify({
                type: "error",
                message: "Failed to handle offer from producer.",
              })
            );
          }
          break;

        case "producerTransportConnect":
          // Handle producer's transport connection
          try {
            const producerFeedId = feedId; // 'feed1', 'feed2', etc.
            const { dtlsParameters } = data;

            const transport = peers[producerFeedId]?.transport;
            if (!transport) {
              console.error(
                `No transport found for producer feedId: ${producerFeedId}`
              );
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: "No transport found for producer.",
                })
              );
              return;
            }

            await transport.connect({ dtlsParameters });
            console.log(
              `Producer transport connected for feedId: ${producerFeedId}`
            );

            // Now, expect the Python client to send 'produce' message with rtpParameters
          } catch (error) {
            console.error(
              `Error handling producerTransportConnect for feedId ${feedId}:`,
              error
            );
            ws.send(
              JSON.stringify({
                type: "error",
                message: "Failed to connect producer transport.",
              })
            );
          }
          break;

        case "produce":
          // Handle 'produce' message from producer, containing rtpParameters
          try {
            const producerFeedId = feedId; // 'feed1', 'feed2', etc.
            const { rtpParameters } = data;
            console.log(
              `Handling produce message for feedId: ${producerFeedId}`,
              rtpParameters
            );

            const transport = peers[producerFeedId]?.transport;
            if (!transport) {
              console.error(
                `No transport found for producer feedId: ${producerFeedId}`
              );
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: "No transport found for producer.",
                })
              );
              return;
            }

            const producer = await transport.produce({
              kind: "video",
              rtpParameters: rtpParameters,
            });

            peers[producerFeedId].producer = producer;
            console.log(`Producer created for feedId: ${producerFeedId}`);

            // Optionally, send confirmation to producer
            ws.send(JSON.stringify({ type: "produced", id: producer.id }));
          } catch (error) {
            console.error(
              `Error handling produce for feedId ${feedId}:`,
              error
            );
            ws.send(
              JSON.stringify({
                type: "error",
                message: "Failed to create producer.",
              })
            );
          }
          break;

        // **Consumer Side Handling**

        case "getRouterRtpCapabilities":
          // Handle frontend request to get router RTP capabilities
          try {
            ws.send(
              JSON.stringify({
                type: "routerRtpCapabilities",
                data: router.rtpCapabilities,
              })
            );
            console.log("Sent routerRtpCapabilities");
          } catch (error) {
            console.error("Error sending routerRtpCapabilities:", error);
          }
          break;

        case "createConsumerTransport":
          // Handle frontend request to create a consumer transport
          try {
            const { feedId: consumerFeedId } = data; // feedId to consume
            console.log(
              `Creating consumer transport for feedId: ${consumerFeedId}`
            );

            const transport = await router.createWebRtcTransport(
              config.mediasoup.webRtcTransport
            );

            // Store transport per consumer client (using ws as key)
            consumers[ws].transport = transport;

            // Send transport params back to frontend
            ws.send(
              JSON.stringify({
                type: "consumerTransportCreated",
                feedId: consumerFeedId,
                data: {
                  id: transport.id,
                  iceParameters: transport.iceParameters,
                  iceCandidates: transport.iceCandidates,
                  dtlsParameters: transport.dtlsParameters,
                },
              })
            );
            console.log(
              `Consumer transport created for feedId: ${consumerFeedId}`
            );
          } catch (error) {
            console.error("Error creating consumer transport:", error);
            ws.send(
              JSON.stringify({
                type: "error",
                message: "Failed to create consumer transport.",
              })
            );
          }
          break;

        case "connectConsumerTransport":
          // Handle frontend request to connect the consumer transport
          try {
            const { feedId: consumerFeedId, dtlsParameters } = data;

            const consumerTransport = consumers[ws]?.transport;
            if (!consumerTransport) {
              console.error("No consumer transport found for this client");
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: "No consumer transport found.",
                })
              );
              return;
            }

            await consumerTransport.connect({ dtlsParameters });
            console.log(
              `Consumer transport connected for feedId ${consumerFeedId}`
            );
          } catch (error) {
            console.error("Error connecting consumer transport:", error);
            ws.send(
              JSON.stringify({
                type: "error",
                message: "Failed to connect consumer transport.",
              })
            );
          }
          break;

        case "consume":
          // Handle frontend request to consume a producer's stream
          try {
            const { feedId: consumerFeedId } = data;
            if (!consumerFeedId) {
              console.error("No feedId provided for consume");
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: "No feedId provided for consume.",
                })
              );
              return;
            }

            const consumerTransport = consumers[ws]?.transport;
            if (!consumerTransport) {
              console.error("No consumer transport found for this client");
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: "No consumer transport found.",
                })
              );
              return;
            }

            const producer = peers[consumerFeedId]?.producer;
            if (!producer) {
              console.error(`No producer found for feedId ${consumerFeedId}`);
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: `No producer found for feedId ${consumerFeedId}`,
                })
              );
              return;
            }

            // Check if the router can consume the producer's RTP capabilities
            const canConsume = router.canConsume({
              producerId: producer.id,
              rtpCapabilities: {}, // You need to provide the consumer's RTP capabilities
            });

            if (!canConsume) {
              console.error("Cannot consume producer's RTP capabilities");
              ws.send(
                JSON.stringify({
                  type: "error",
                  message: "Cannot consume producer's RTP capabilities",
                })
              );
              return;
            }

            // Create consumer
            const consumer = await consumerTransport.consume({
              producerId: producer.id,
              rtpCapabilities: {}, // Provide the actual RTP capabilities of the consumer
              paused: false,
            });

            // Add consumer to the list
            consumers[ws].consumers[consumerFeedId] = consumer;

            // Send consumer parameters to frontend
            ws.send(
              JSON.stringify({
                type: "candidate",
                sdpMid: candidate.sdpMid,
                sdpMLineIndex: candidate.sdpMLineIndex,
                candidate: candidate.candidate,
                feedId: producerFeedId,
              })
            );

            console.log(`Consumer created for feedId ${consumerFeedId}`);
          } catch (error) {
            console.error("Error creating consumer:", error);
            ws.send(
              JSON.stringify({
                type: "error",
                message: "Failed to create consumer.",
              })
            );
          }
          break;

        default:
          console.error("Unknown message type:", data.type);
      }
    });

    ws.on("close", () => {
      console.log(`WebSocket connection closed for feedId ${feedId}`);

      // Cleanup for producer
      if (peers[feedId]) {
        if (peers[feedId].producer) {
          peers[feedId].producer.close();
        }
        if (peers[feedId].transport) {
          peers[feedId].transport.close();
        }
        if (peers[feedId].pc) {
          peers[feedId].pc.close();
        }
        delete peers[feedId];
      }

      // Cleanup for consumer
      if (consumers[ws]) {
        if (consumers[ws].consumers) {
          Object.values(consumers[ws].consumers).forEach((consumer) => {
            consumer.close();
          });
        }
        if (consumers[ws].transport) {
          consumers[ws].transport.close();
        }
        delete consumers[ws];
      }

      // Optionally, terminate Python process if it's a producer connection
      if (pythonProcesses[feedId]) {
        console.log(`Terminating Python process for feedId: ${feedId}`);
        pythonProcesses[feedId].kill();
        delete pythonProcesses[feedId];
      }
    });
  });
};

module.exports = async (wss) => {
    // Setup Mediasoup Worker and Router
    const worker = await mediasoup.createWorker(config.mediasoup.worker);
    const router = await worker.createRouter({ mediaCodecs: config.mediasoup.router.mediaCodecs });

    wss.on('connection', async (ws, req) => {
        console.log('New WebSocket connection');

        // Initialize per-socket data
        consumers[ws] = {
            producerTransport: null,
            producer: null,
            consumerTransport: null,
            consumer: null,
        };

        ws.on('message', async (message) => {
            let data;
            try {
                data = JSON.parse(message);
            } catch (e) {
                console.error('Invalid JSON:', e);
                ws.send(JSON.stringify({ type: 'error', message: 'Invalid JSON' }));
                return;
            }

            const { type, feedId, data: msgData } = data;

            switch (type) {
                // Handle Producer Signaling
                case 'offer':
                    await handleProducerOffer(ws, feedId, msgData);
                    break;

                case 'candidate':
                    await handleProducerCandidate(ws, feedId, msgData);
                    break;

                // Handle Consumer Signaling
                case 'createConsumerTransport':
                    await handleCreateConsumerTransport(ws, feedId);
                    break;

                case 'connectConsumerTransport':
                    await handleConnectConsumerTransport(ws, feedId, msgData);
                    break;

                case 'consume':
                    await handleConsume(ws, feedId, msgData);
                    break;

                case 'consumerCandidate':
                    await handleConsumerCandidate(ws, feedId, msgData);
                    break;

                default:
                    console.warn('Unhandled message type:', type);
            }
        });

        ws.on('close', () => {
            // Clean up on WebSocket close
            console.log('WebSocket connection closed');
            // Close Mediasoup transports and consumers if any
            if (consumers[ws].producerTransport) consumers[ws].producerTransport.close();
            if (consumers[ws].consumerTransport) consumers[ws].consumerTransport.close();
            if (consumers[ws].consumer) consumers[ws].consumer.close();
            delete consumers[ws];
        });
    });

    // Handler Functions (Implement these based on your Mediasoup setup)
    const handleProducerOffer = async (ws, feedId, offer) => {
        try {
            const producerFeedId = feedId; // 'feed1', 'feed2', etc.
            console.log(`Handling offer for producer feedId: ${producerFeedId}`);
    
            const offerSdp = offer.sdp;
            const offerType = offer.type_desc;
    
            // Create a WebRTC RTCPeerConnection to handle the offer
            const pc = new RTCPeerConnection({
                iceServers: config.mediasoup.iceServers || [],
            });
    
            // Handle ICE candidates from the server side
            pc.onicecandidate = ({ candidate }) => {
                if (candidate) {
                    ws.send(JSON.stringify({
                        type: "candidate",
                        candidate: {
                            sdpMid: candidate.sdpMid,
                            sdpMLineIndex: candidate.sdpMLineIndex,
                            candidate: candidate.candidate
                        },
                        feedId: producerFeedId
                    }));
                    console.log(`Sent ICE candidate for feedId: ${producerFeedId}`);
                }
            };
    
            // Set remote description with the offer from producer
            await pc.setRemoteDescription(new RTCSessionDescription({ type: offerType, sdp: offerSdp }));
            console.log(`Set remote description for feedId: ${producerFeedId}`);
    
            // Create an answer
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            console.log(`Created and set local answer for feedId: ${producerFeedId}`);
    
            // Send the answer back to the producer
            ws.send(JSON.stringify({
                type: "answer",
                sdp: pc.localDescription.sdp,
                type_desc: pc.localDescription.type,
                feedId: producerFeedId,
            }));
            console.log(`Sent answer for feedId: ${producerFeedId}`);
    
            // After setting up the connection, create a transport in Mediasoup
            const transport = await router.createWebRtcTransport(config.mediasoup.webRtcTransport);
    
            peers[producerFeedId] = { transport, pc };
    
            // Send transport parameters to the producer
            ws.send(JSON.stringify({
                type: "producerTransportCreated",
                data: {
                    id: transport.id,
                    iceParameters: transport.iceParameters,
                    iceCandidates: transport.iceCandidates,
                    dtlsParameters: transport.dtlsParameters,
                },
            }));
            console.log(`Created transport for producer feedId: ${producerFeedId}`);
        } catch (error) {
            console.error(`Error handling offer from producer feedId ${feedId}:`, error);
            ws.send(JSON.stringify({
                type: "error",
                message: "Failed to handle offer from producer.",
            }));
        }
    };
    const handleProducerCandidate = async (ws, feedId, candidate) => {
        // Add ICE candidate to Producer Transport
    };

    const handleCreateConsumerTransport = async (ws, feedId) => {
        // Create a Mediasoup transport for the consumer
        const transport = await router.createWebRtcTransport(config.mediasoup.webRtcTransport);
        consumers[ws].consumerTransport = transport;

        ws.send(JSON.stringify({
            type: 'consumerTransportCreated',
            feedId,
            data: {
                id: transport.id,
                iceParameters: transport.iceParameters,
                iceCandidates: transport.iceCandidates,
                dtlsParameters: transport.dtlsParameters,
            },
        }));
    };

    const handleConnectConsumerTransport = async (ws, feedId, dtlsParameters) => {
        // Connect the consumer transport with DTLS parameters
        await consumers[ws].consumerTransport.connect({ dtlsParameters });
    };

    const handleConsume = async (ws, feedId, msgData) => {
        const { producerId, rtpCapabilities } = msgData;

        // Check if Router supports the RTP capabilities of the Consumer
        const canConsume = router.canConsume({
            producerId,
            rtpCapabilities,
        });

        if (!canConsume) {
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Cannot consume',
            }));
            return;
        }

        // Create Consumer
        const consumer = await consumers[ws].consumerTransport.consume({
            producerId,
            rtpCapabilities,
            paused: false,
        });

        consumers[ws].consumer = consumer;

        ws.send(JSON.stringify({
            type: 'consumerCreated',
            data: {
                id: consumer.id,
                producerId,
                kind: consumer.kind,
                rtpParameters: consumer.rtpParameters,
            },
            feedId,
        }));

        consumer.on('transportclose', () => {
            consumer.close();
        });

        consumer.on('producerclose', () => {
            ws.send(JSON.stringify({ type: 'producerClosed', feedId }));
        });
    };

    const handleConsumerCandidate = async (ws, feedId, candidate) => {
        // Add ICE candidate to Consumer Transport
        if (consumers[ws].consumerTransport && candidate) {
            await consumers[ws].consumerTransport.addIceCandidate(candidate);
        }
    };
};
