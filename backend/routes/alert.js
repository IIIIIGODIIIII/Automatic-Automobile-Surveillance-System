const express = require('express');
const { getAlerts, addAlert } = require('../controller/alert');

const router = express.Router();

router.get('/', getAlerts)
      .post('/', addAlert);

exports.router = router;