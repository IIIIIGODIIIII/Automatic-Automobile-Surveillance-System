const mongoose = require('mongoose');
const {Schema} = mongoose;

const RegisteredVechileSchema = new Schema({
    number:{
        type: String,
        required: true,
        unique: true
    },
    owner:{
        type: String,
        required: true
    },
    model:{
        type: String,
        required: true
    },
    year:{
        type: Number,
        required: true
    }
})

exports.RegisteredVechile = mongoose.model('RegisteredVechile', RegisteredVechileSchema);