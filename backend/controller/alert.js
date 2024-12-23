const {Alert} = require('../models/Alert');

exports.getAlerts = async (req, res) => {
    try {
        const alerts = await Alert.find();
        res.json(alerts);
    } catch (error) {
        res.status(400).json({message: error.message});
    }
}

exports.addAlert = async (req, res) => {
    const alert = new Alert({
        vehicleNumber: req.body.vehicleNumber,
        speed: req.body.speed,
        location: "Main Gate Road",
        timestamp: new Date().toISOString(),
    });

    try {
        const newAlert = await alert.save();
        res.status(201).json(newAlert);
    } catch (error) {
        res.status(400).json({message: error.message});
    }
}