const express = require('express');
const fs = require('fs');
const router = express.Router();

/* GET home page. */
router.get('/', function (req, res, next) {
    res.send(JSON.parse(fs.readFileSync("kerberus.json")));
});

/* GET home page. */
router.get('/:name', function (req, res, next) {
    if (req.params.name == "") {
        res.send(JSON.parse(fs.readFileSync("kerberus.json")));
    } else {
        lista = JSON.parse(fs.readFileSync("kerberus.json")).find(o => o.name === req.params.name);
        res.send(lista);
    }
});

module.exports = router;