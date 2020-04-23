const express = require('express');
const fs = require('fs');
const router = express.Router();

/* GET home page. */
router.get('/', function (req, res, next) {
    ok = false;
    if (fs.existsSync("kerberus.pid")) {
        spid = fs.readFileSync("kerberus.pid", 'utf8').toString();
        if (spid != "") {
            pid = parseInt(spid);
            console.log("======>>>>>>")
            console.log(process.kill(pid, 0))
            ok = true;
        }
    }
    if (ok) {
        lista = JSON.parse(fs.readFileSync("kerberus.json"))
        for (i=0;i<lista.length;i++) {
            ok = ok && (lista[i]['status'] === 'running' || lista[i]['status'] === 'stopped');
        }
    }
    res.send({ status: ok });
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