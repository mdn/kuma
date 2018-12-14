/**
 * KumaScript HTTP service
 * Provides the HTTP service for document processing
 * @prettier
 */
const path = require('path');
const url = require('url');

const express = require('express');
const morgan = require('morgan');
const request = require('request');
const winston = require('winston');

const config = require('./config.js');
const firelogger = require('./firelogger.js');
const Templates = require('./templates.js');
const render = require('./render.js');

// TODO: figure out the newrelic config details and re-enable before deploying
//var newrelic_conf = ks_conf.nconf.get('newrelic');
//if (newrelic_conf && newrelic_conf.license_key) require('newrelic');

class Server {
    /**
     * Build the service, but do not listen yet.
     */
    constructor() {
        const app = (this.app = express());

        // This will raise an error if the macros are not found
        this.templates = new Templates(config.macrosDirectory);

        // Configure a logger that pipes to the winston logger.
        if (config.logging) {
            var logger = morgan(
                ':remote-addr - - [:date] ":method :url ' +
                    'HTTP/:http-version" :status :res[content-length] ' +
                    '":referrer" ":user-agent" :response-time',
                {
                    stream: {
                        write: function(s) {
                            winston.info(s.trim(), {
                                source: 'server',
                                pid: process.pid
                            });
                        }
                    }
                }
            );

            app.use(logger);
        }

        // Define a response.log.error() function that allows us to send
        // KumaScript error messages back to Kuma in HTTP response headers
        app.use(firelogger({ logger: config.logging ? winston.info : null }));

        // Set up HTTP routing.
        // First we have various utility endpoints:
        app.get('/', this.root.bind(this));
        app.get('/revision/?', this.revision.bind(this));
        app.get('/healthz/?', this.healthz.bind(this));
        app.get('/readiness/?', this.readiness.bind(this));
        app.get('/macros/?', this.macros.bind(this));

        // This is the main template-rendering endpoint
        app.post('/docs/', this.docs.bind(this));
    }

    /**
     * Start the service listening
     *
     * @param {port} number
     */
    listen(port) {
        port = port || config.port;
        this.server = this.app.listen(port);
    }

    /**
     * Close down the service
     */
    close() {
        if (this.server) {
            this.server.close();
        }
    }

    /**
     * This is the "hello world" endpoint for GET /
     */
    root(req, res) {
        res.send('<html><body><p>Hello from KumaScript!</p></body></html>');
    }

    /**
     * #### GET /revision
     *
     * Return the value of the git commit hash for HEAD.
     */
    revision(req, res) {
        res.set({ 'content-type': 'text/plain; charset=utf-8' }).send(
            process.env.REVISION_HASH || 'undefined'
        );
    }

    /**
     * A "liveness" endpoint for use by Kubernetes or other
     * similar systems. A successful response from this endpoint
     * simply proves that this Express app is up and running. It
     * doesn't mean that its supporting services (like the macro
     * loader and the document service) can be successfully used
     * from this service.
     */
    healthz(req, res) {
        res.sendStatus(204);
    }

    /**
     * A "readiness" endpoint for use by Kubernetes or other
     * similar systems. A successful response from this endpoint goes
     * a step further and means not only that this Express app is up
     * and running, but also that one or more macros have been found
     * and that the document service is ready.
     */
    readiness(req, res) {
        // If we're running, then we're ready to go. But we need to make
        // sure that the Kuma API server is ready for us to make requests of.
        // This endpoint is going to be hit every second or two. Let's not
        // create extra traffic by hitting the Kuma endpoint each time.
        // If Kuma was ready sometime in the last minute, we'll assume
        // it is still ready.
        if (this.kumaReadyTime && Date.now() - this.kumaReadyTime < 60000) {
            // We got a positive response from Kuma within the last minute
            // so we don't need to check again now.
            res.sendStatus(204);
        } else {
            // If we've never checked Kuma's readiness or it has been a while
            // then we should check
            const kumaReadiness = url.resolve(config.documentURL, 'readiness');
            request.get(kumaReadiness, (err, resp, body) => {
                if (!err && (resp.statusCode >= 200 && resp.statusCode < 400)) {
                    this.kumaReadyTime = Date.now();
                    res.sendStatus(204);
                } else {
                    this.kumaReadyTime = 0;
                    res.status(503).send(
                        `Service unavailable (Kuma not ready: ${
                            err ? err : body
                        })`
                    );
                }
            });
        }
    }

    /**
     * #### GET /macros
     *
     * Get JSON of available macros (also known as templates)
     */
    macros(req, res) {
        let macros = [];
        for (let filepath of this.templates.getTemplateMap().values()) {
            macros.push({
                // Don't use the name from the map because it is already
                // in lowercase: take the original name from the file instead
                name: path.parse(filepath).name,
                // Return just the part of the filename relative to
                // the macros directory
                filename: filepath.slice(config.macrosDirectory.length)
            });
        }

        res.json({
            loader: 'FileLoader',
            can_list_macros: true,
            macros: macros
        });
    }

    /**
     * #### POST /docs/
     *
     * Process POST body, respond with result of macro evaluation
     */
    docs(request, response) {
        let body = '';
        request.setEncoding('utf8');
        request.on('data', chunk => {
            body += chunk;
        });
        request.on('end', async () => {
            try {
                let variables = getVariables();
                let [result, errors] = await render(
                    body,
                    this.templates,
                    variables
                );

                // If there were errors, we log them which (because of the
                // firelogger middleware) adds them to the response headers
                // so that Kuma can report them.
                for (let error of errors) {
                    response.log.error(error.message, {
                        name: 'kumascript',
                        template: '%s: %s',
                        args: [error.name, error.message, error.options]
                    });
                }
                response.send(result);
            } catch (e) {
                // If all else fails, just send back the unrendered body
                response.log.error(e.message, {
                    name: 'kumascript',
                    template: '%s: %s',
                    args: [e.name, e.message, e.options]
                });
                response.send(body);
            }
        });

        // Kuma passes environment variables like the document title, language
        // and slug to us via x-kumascript-env-<varname> headers on the request.
        // this function extracts those variables from the request.
        function getVariables() {
            let variables = {};
            for (let header of Object.keys(request.headers)) {
                if (header.startsWith(config.envHeaderPrefix)) {
                    let key = header.slice(config.envHeaderPrefix.length);
                    let raw = request.headers[header];
                    let value = JSON.parse(
                        Buffer.from(raw, 'base64').toString()
                    );
                    variables[key] = value;
                }
            }

            // We have macros that expect certain variables to be defined.
            // So we need to ensure that they have a value even if nothing
            // was passed by the server
            variables.slug = variables.slug || '';
            variables.title = variables.title || '';
            variables.locale = variables.locale || 'en-US';
            variables.url = variables.url || '';

            // Pass the HTTP cache control header through these variables.
            variables.cache_control = request.get('cache-control') || '';

            // TODO: This is ugly. We could change the macros that use these
            // and put the base urls directly on the mdn object instead.
            variables.interactive_examples = {
                base_url: config.interactiveExamplesURL
            };
            variables.live_samples = { base_url: config.liveSamplesURL };

            return variables;
        }
    }
}

module.exports = Server;
