/**
 * Command line KumaScript server runner
 * @prettier
 */

const util = require('util');
const http = require('http');
const net = require('net');
const winston = require('winston');

const config = require('./src/config.js');
const Server = require('./src/server.js');

// Logging
winston.add(new winston.transports.Console());
const log = winston;

// Start up a server instance.
log.info(`KumaScript server starting (PID ${process.pid}).`);
var server = new  Server();
log.info(`KumaScript server listening on port ${config.port}`);
server.listen(config.port);

function exit () {
    log.info(`KumaScript server (PID ${process.pid}) exiting.`);
    server.close();
    process.exit(0);
}

// More gracefully handle some common exit conditions...
process.on('SIGINT', function () {
    log.info("Received SIGINT, exiting...");
    exit();
});
process.on('SIGTERM', function () {
    log.info("Received SIGTERM, exiting...");
    exit();
});
process.on('uncaughtException', function (err) {
    log.error('uncaughtException:', err.message);
    log.error(err.stack);
    exit();
});
