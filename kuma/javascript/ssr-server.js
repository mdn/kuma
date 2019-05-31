/* eslint-disable no-console */
/*
 * This is a simple Express server for performing server side rendering
 * of our React UI. The main endpoint is POST /ssr, and it invokes the
 * ssr() function from dist/ssr.js (which is webpacked from src/ssr.jsx).
 */

// Start New Relic logging if it is configured.
// The require('newrelic') must be the very first require in the
// file in order for reporting to work correctly.
if (process.env.NEW_RELIC_LICENSE_KEY && process.env.NEW_RELIC_APP_NAME) {
    console.log('Starting New Relic logging for the SSR server.');
    require('newrelic');
}

const express = require('express'); // Express server framework
const morgan = require('morgan');

const ssr = require('./dist/ssr.js'); // Function to do server-side rendering

// Configuration
const PID = process.pid;
const PORT = parseInt(process.env.SSR_PORT) || 8000;
const MAX_BODY_SIZE = 1024 * 1024; // 1 megabyte max JSON payload

// We're using the Express server framework
const app = express();

// Log all requests, so we get timing data for SSR.
app.use(morgan('tiny'));

// Handle JSON payloads in POST requests, putting data in req.body
app.use(express.json({ limit: MAX_BODY_SIZE }));

// A hello world endpoint for easy verification that the service is running
app.get('/', (req, res) => {
    res.send('<html><body><p>SSR server ready</p></body></html>');
});

// revision, health and readiness endpoints used (I think) by Kubernetes
app.get('/revision/?', (req, res) => {
    res.set({ 'Content-Type': 'text/plain; charset=utf-8' }).send(
        process.env.REVISION_HASH || 'undefined'
    );
});
app.get('/healthz/?', (req, res) => {
    res.sendStatus(204);
});
app.get('/readiness/?', (req, res) => {
    res.sendStatus(204);
});

/*
 * This is the main endpoint. It expects document API data as application/json
 * in the POST request body and returns rendered HTML in the response body.
 * The response is an HTML fragment, not a complete document and it is not
 * intended for display on its own. The content type of the response is
 * text/plain instead of text/html to make it clear that the response should
 * not be parsed, escaped, or displayed as HTML.
 */
app.post('/ssr/:componentName', (req, res) => {
    res.set({ 'Content-Type': 'text/plain; charset=utf-8' }).send(
        ssr(req.params.componentName, req.body)
    );
});

if (require.main === module) {
    // If we're actually being run directly with node, then
    // set up signal handlers and start listening for connections

    // More gracefully handle some common exit conditions...
    const exit = function() {
        console.log(`SSR server (PID ${PID}) exiting.`);
        server.close();
        process.exit(0);
    };
    process.on('SIGINT', function() {
        console.log('Received SIGINT, exiting...');
        exit();
    });
    process.on('SIGTERM', function() {
        console.log('Received SIGTERM, exiting...');
        exit();
    });
    process.on('uncaughtException', function(err) {
        console.error('uncaughtException:', err.message);
        console.error(err.stack);
        exit();
    });

    // And finally, start listening for connections.
    const server = app.listen(PORT, () => {
        console.log(`SSR server (PID ${PID}) listening on port ${PORT}.`);
    });
} else {
    // If we've just been required (in a test, for example) then
    // we just export the app object and don't actually start listening.
    module.exports = app;
}
