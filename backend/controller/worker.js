// worker.js
const mediasoup = require('mediasoup');
const config = require('../config');

let workerInstance = null;

const createWorker = async () => {
    if (workerInstance) {
        console.log('Mediasoup worker already created with PID:', workerInstance.pid);
        console.trace('createWorker called from:');
        return workerInstance;
    }
    try {
        console.trace('createWorker is being called from:');
        console.log('Creating Mediasoup worker...');
        const worker = await mediasoup.createWorker({
            logLevel: config.mediasoup.worker.loglevel,
            logTags: config.mediasoup.worker.logtags,
            rtcMinPort: config.mediasoup.worker.rtcMinPort,
            rtcMaxPort: config.mediasoup.worker.rtcMaxPort,
        });
        console.log(`Mediasoup worker created with PID: ${worker.pid}`);

        worker.on('died', () => {
            console.error(`Mediasoup worker died, exiting in 2 seconds... [pid:${worker.pid}]`);
            setTimeout(() => process.exit(1), 2000);
        });

        workerInstance = worker;
        return worker;
    } catch (error) {
        console.error('Error creating Mediasoup worker:', error);
        throw error;
    }
};

module.exports = { createWorker };