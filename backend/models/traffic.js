const mongoose = require('mongoose');
const {Schema} = mongoose;

const TrafficSchema = new Schema({
//vechile number should have a reference to the number in registered vechiles
    vehicleNumber :{
        type: String,
        required: true,
        ref: 'RegisteredVechile'
    },
    timestamp : {
        type: Date,
        required: true
    },
})

exports.Traffic = mongoose.model('Traffic', TrafficSchema);
    



