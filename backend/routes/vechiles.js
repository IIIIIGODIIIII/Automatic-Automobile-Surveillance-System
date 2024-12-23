const express = require('express');
const { addVechile, getVechiles } = require('../controller/vechiles');

const router = express.Router();

router.post('/register', addVechile)
      .get('/', getVechiles);

exports.router = router;