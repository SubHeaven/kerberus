const express = require('express');
const fs = require('fs');
const router = express.Router();

/* GET home page. */
router.get('/', function (req, res, next) {
    res.send({ status: true });
});

/* GET home page. */
router.get('/:name', function (req, res, next) {
    if (req.params.name == "") {
        res.send({ status: true });
    } else {
        lista = JSON.parse(fs.readFileSync("kerberus.json")).find(o => o.name === req.params.name);
        if (typeof lista == "undefined") {
            res.send({ status: false });
        } else {
            res.send({ status: true });
        }
    }
});

module.exports = router;