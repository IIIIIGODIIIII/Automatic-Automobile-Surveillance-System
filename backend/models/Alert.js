const mongoose = require('mongoose');
const {Schema} = mongoose;

const AlertSchema = new Schema({
    vehicleNumber : {
        type: String,
        required: true
    },
    speed: {
        type: Number,
        required: true
    },
    location : {
        type: String,
        required: true
    },
    timestamp : {
        type: Date,
        required: true
    }
} )

exports.Alert = mongoose.model('Alert', AlertSchema);