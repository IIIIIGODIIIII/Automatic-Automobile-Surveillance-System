// config.js

module.exports = {
    mediasoup: {
        worker: {
            rtcMinPort: 40000,
            rtcMaxPort: 49999,
            logLevel: "warn",
            logTags: [
                "info",
                "ice",
                "dtls",
                "rtp",
                "srtp",
                "rtcp",
                "rtp-hdrext",
                "srtp",
                "ice-lite"
            ],
        },
        router: {
            mediaCodecs: [
                {
                    kind: "audio",
                    mimeType: "audio/opus",
                    clockRate: 48000,
                    channels: 2
                },
                {
                    kind: "video",
                    mimeType: "video/VP8",
                    clockRate: 90000,
                    parameters: {}
                },
                {
                    kind: "video",
                    mimeType: "video/H264",
                    clockRate: 90000,
                    parameters: {
                        "packetization-mode": 1,
                        "profile-level-id": "42001f",
                        "level-asymmetry-allowed": 1
                    }
                }
            ],
        },
        webRtcTransport: {
            listenIps: [
                { ip: "127.0.0.1", announcedIp: null } // Replace with your server's IP for production
            ],
            enableUdp: true,
            enableTcp: true,
            preferUdp: true,
            initialAvailableOutgoingBitrate: 1000000
        }
    },
    // Add other configurations as needed
};