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
const Sentry = require('@sentry/node');

const ssr = require('./dist/ssr.js'); // Function to do server-side rendering

// Configuration
const PID = process.pid;
const PORT = parseInt(process.env.SSR_PORT) || 8000;

// Some documents, with lots of Unicode, get very large when Python
// serializes it to a binary string. For example,
// https://developer.mozilla.org/ja/docs/Web/API/Window when turned into
// a JSON string, by Python, becomes a string of length ~1.1MB.
// Add a little extra just to be on the safe side.
const MAX_BODY_SIZE = 1024 * 1024 * 5; // 5 megabyte max JSON payload

// We're using the Express server framework
const app = express();

// Configure and initialize Sentry if a DSN has been provided.
if (process.env.SENTRY_DSN) {
    console.log('Configuring Sentry for the SSR server.');
    let options = {
        dsn: process.env.SENTRY_DSN
    };
    if (process.env.REVISION_HASH) {
        options.release = process.env.REVISION_HASH;
    }
    if (process.env.SENTRY_ENVIRONMENT) {
        options.environment = process.env.SENTRY_ENVIRONMENT;
    }
    Sentry.init(options);
    // The request handler must be the first middleware on the app
    app.use(Sentry.Handlers.requestHandler());
} else {
    console.warn('SENTRY_DSN is not available so sentry is not initialized.');
}

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
    res.json(ssr(req.params.componentName, req.body));
});

// Important that this is defined *after* the request handlers have been
// added otherwise Sentry won't automatically hook in.
if (process.env.SENTRY_DSN) {
    // The error handler must be before any other error middleware and after
    // all controllers.
    app.use(Sentry.Handlers.errorHandler());
}

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
