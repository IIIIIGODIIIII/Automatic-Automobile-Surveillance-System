const {Traffic} = require('../models/traffic');

exports.getTraffic = async (req, res) => {
    try {
        //calculate the no of traffic on each day so that it can be passed to the graph to plot it 
        const traffic = await Traffic.aggregate([
            {
                $group: {
                    _id: { $dateToString: { format: "%Y-%m-%d", date: "$timestamp" } },
                    count: { $sum: 1 }
                }
            }
        ]);


        res.json(traffic);
    } catch (error) {
        res.status(400).json({message: error.message});
    }
}

exports.postTraffic = async (req, res) => {
    const traffic = new Traffic({
        vehicleNumber: req.body.vehicleNumber,
        timestamp: req.body.timestamp
    });

    try {
        const newTraffic = await traffic.save();
        res.status(201).json(newTraffic);
    } catch (error) {
        res.status(400).json({message: error.message});
    }
}