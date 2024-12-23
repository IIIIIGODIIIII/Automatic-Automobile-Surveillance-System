const {RegisteredVechile} = require('../models/RegisteredVechile');

exports.getVechiles = async (req, res) => {
    try {
        const vechiles = await RegisteredVechile.find();
        res.json(vechiles);
    } catch (error) {
        res.status(400).json({message: error.message});
    }
}

exports.addVechile = async (req, res) => {
    const vechile = new RegisteredVechile({
        number: req.body.number,
        owner: req.body.owner,
        model: req.body.model,
        year: req.body.year
    });

    try {
        
        const vechileExist = await RegisteredVechile.findOne({number
            : req.body.number});
        if(vechileExist) return res.status(400).json({message: "Vechile already registered"});

        const newVechile = await vechile.save();
        res.status(201).json(newVechile);
    } catch (error) {
        res.status(400).json({message: error.message});
    }
}