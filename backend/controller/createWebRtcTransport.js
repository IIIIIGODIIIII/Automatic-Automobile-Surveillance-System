// createWebRtcTransport.js
const mediasoup = require('mediasoup');
const config = require('../config');

const createWebRtcTransport = async (router) => {
    try {
        console.log('Creating WebRTC Transport...');
        const transport = await router.createWebRtcTransport({
            listenIps: config.mediasoup.webRtcTransport.listenIps,
            enableUdp: true,
            enableTcp: true,
            preferUdp: true,
            initialAvailableOutgoingBitrate: config.mediasoup.webRtcTransport.initialAvailableOutgoingBitrate,
        });
        console.log(`WebRTC Transport created with ID: ${transport.id}`);

        transport.on('dtlsstatechange', (dtlsState) => {
            console.log(`Transport DTLS state changed to ${dtlsState}`);
            if (dtlsState === 'closed') {
                console.log(`Transport ${transport.id} DTLS state is closed, closing transport...`);
                transport.close();
            }
        });

        transport.on('close', () => {
            console.log('WebRTC Transport closed');
        });

        const params = {
            id: transport.id,
            iceParameters: transport.iceParameters,
            iceCandidates: transport.iceCandidates,
            dtlsParameters: transport.dtlsParameters,
        };

        console.log('WebRTC Transport parameters:', JSON.stringify(params, null, 2));

        return { transport, params };
    } catch (error) {
        console.error('Error creating WebRTC Transport:', error);
        throw error;
    }
};

module.exports = { createWebRtcTransport };