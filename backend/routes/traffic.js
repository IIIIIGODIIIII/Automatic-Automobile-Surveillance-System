const express = require('express');
const { postTraffic, getTraffic } = require('../controller/traffic');
const router = express.Router();

router.post('/',postTraffic )
      .get('/',getTraffic);

exports.router = router;