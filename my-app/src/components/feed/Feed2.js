// Feed2.js

import React, { useEffect, useState, useRef } from 'react';
import LiveFeed from './LiveFeed';

const Feed2 = ({ feedId, location }) => {
    const [videoSrc, setVideoSrc] = useState(null);
    const [ws, setWs] = useState(null);
    const pcRef = useRef(null);

    useEffect(() => {
        const signalingUrl = 'ws://localhost:8000/ws';
        const socket = new WebSocket(signalingUrl);
        setWs(socket);

        socket.onopen = () => {
            console.log('WebSocket connected');

            // Initialize as Consumer
            socket.send(JSON.stringify({
                type: 'init',
                role: 'consumer',
                feedId: feedId,
            }));

            // Create Consumer Transport
            socket.send(JSON.stringify({
                type: 'createConsumerTransport',
                feedId: feedId,
            }));
        };

        socket.onmessage = async (message) => {
            const data = JSON.parse(message.data);
            console.log('Received message:', data);

            switch (data.type) {
                case 'initSuccess':
                    console.log("Consumer initialized successfully.");
                    break;

                case 'consumerTransportCreated':
                    await connectConsumerTransport(data.data);
                    break;

                case 'consumerTransportConnected':
                    console.log("Consumer transport connected.");
                    break;

                case 'consumerCreated':
                    await setupConsumer(data.data);
                    break;

                case 'error':
                    console.error('Error from server:', data.message);
                    break;

                default:
                    console.warn('Unhandled message type:', data.type);
            }
        };

        socket.onerror = (err) => {
            console.error('WebSocket error:', err);
        };

        socket.onclose = () => {
            console.log('WebSocket disconnected');
            cleanup();
        };

        return () => {
            socket.close();
            cleanup();
        };
    }, [feedId]);

    const connectConsumerTransport = async (transportParams) => {
        const pc = new RTCPeerConnection({
            iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        });
        pcRef.current = pc;

        pc.ontrack = (event) => {
            console.log('Received track:', event.streams);
            setVideoSrc(event.streams[0]);
        };

        pc.onicecandidate = (event) => {
            if (event.candidate) {
                ws.send(JSON.stringify({
                    type: 'consumerCandidate',
                    candidate: event.candidate,
                    transportId: transportParams.id,
                    feedId: feedId,
                }));
            }
        };

        try {
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);

            ws.send(JSON.stringify({
                type: 'connectConsumerTransport',
                transportId: transportParams.id,
                dtlsParameters: pc.localDescription,
                feedId: feedId,
            }));
        } catch (error) {
            console.error('Error creating or sending answer:', error);
        }
    };

    const setupConsumer = async (consumerData) => {
        if (!pcRef.current) {
            console.error('PeerConnection not established');
            return;
        }

        const { id, producerId, kind, rtpParameters } = consumerData;

        ws.send(JSON.stringify({
            type: 'consume',
            consumerId: id,
            producerId: producerId,
            rtpCapabilities: {
                codecs: [
                    {
                        mimeType: "video/VP8",
                        clockRate: 90000,
                        channels: 0,
                        parameters: {},
                    },
                ],
                headerExtensions: [
                    {
                        uri: "urn:ietf:params:rtp-hdrext:toffset",
                        localId: 1,
                        preferredId: 1,
                        preferredEncrypt: true,
                    },
                ],
                fecMechanisms: [],
            },
            feedId: feedId,
        }));
    };

    const cleanup = () => {
        if (pcRef.current) {
            pcRef.current.close();
            pcRef.current = null;
        }
        if (videoSrc) {
            videoSrc.getTracks().forEach(track => track.stop());
            setVideoSrc(null);
        }
    };

    return (
        <LiveFeed
            feedId={feedId}
            location={location}
            videoSrc={videoSrc}
            isProducer={false}
        />
    );
};

export default Feed2;