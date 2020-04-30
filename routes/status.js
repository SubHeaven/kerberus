const cors = require('cors');
const express = require('express');
const fs = require('fs');
const MongoClient = require('mongodb').MongoClient;
const router = express.Router();

/* GET home page. */
router.get('/', cors({ origin: ['http://127.0.0.1:1160', 'http://127.0.0.1:1560', 'http://192.168.254.216:1560'] }), function (req, res, next) {
    ok = false;
    if (fs.existsSync("kerberus.pid")) {
        spid = fs.readFileSync("kerberus.pid", 'utf8').toString();
        if (spid != "") {
            pid = parseInt(spid);
            ok = true;
        }
    }
    if (ok) {
        (async function consultarServicos() {
            const client = new MongoClient('mongodb://localhost:27017', { useUnifiedTopology: true });
            await client.connect();
            const db = client.db('iacon');
            let r = await db.collection('kerberus_services').find().toArray();
            for (i=0;i<r.length;i++) {
                ok = ok && (r[i]['status'] === 'running' || r[i]['status'] === 'stopped');
            }
        })().catch(function(error) {
            console.log(error);
            console.log("error");
        });
        // lista = JSON.parse(fs.readFileSync("kerberus.json"))
        // for (i=0;i<lista.length;i++) {
        //     ok = ok && (lista[i]['status'] === 'running' || lista[i]['status'] === 'stopped');
        // }
    }
    res.send({ status: ok });
});

/* GET home page. */
router.get('/:name', function (req, res, next) {
    if (req.params.name == "") {
        res.send({ status: true });
    } else {
        (async function consultarServicos() {
            const client = new MongoClient('mongodb://localhost:27017', { useUnifiedTopology: true });
            await client.connect();
            const db = client.db('iacon');
            let r = await db.collection('kerberus_services').find({name: req.params.name}).toArray();
            res.send({ status: (r.length > 0) });
        })().catch(function(error) {
            console.log(error);
            res.send("error");
        });
        // lista = JSON.parse(fs.readFileSync("kerberus.json")).find(o => o.name === req.params.name);
        // if (typeof lista == "undefined") {
        //     res.send({ status: false });
        // } else {
        //     res.send({ status: true });
        // }
    }
});

module.exports = router;