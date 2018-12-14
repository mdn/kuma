/**
 * @prettier
 */
const fs = require('fs');
const path = require('path');

const express = require('express');
const request = require('request');

const Server = require('../src/server.js');
const config = require('../src/config.js');

const FIXTURES_PATH = path.join(__dirname, 'fixtures', 'server');
const KUMA_PORT = 11111;
const KUMASCRIPT_PORT = 22222;

// Customize KumaScript configuration options for testing
config.port = KUMASCRIPT_PORT;
config.documentURLTemplate = `http://localhost:${KUMA_PORT}/documents/{path}.txt`;
config.documentURL = `http://localhost:${KUMA_PORT}`;
config.macrosDirectory = __dirname + '/fixtures/server/macros/';
config.logging = false;

/**
 * Creates an HTTP server for fixtures
 */
function createKumaServer() {
    let app = express();

    app.use(function(req, res, mw_next) {
        // Force a delay, which tickles async bugs in need of fixes
        setTimeout(mw_next, 50);
    });

    app.use(express.static(FIXTURES_PATH));
    let kuma_server = app.listen(KUMA_PORT);
    app.close = function() {
        kuma_server.close();
    };

    return app;
}

function getURL(uri) {
    return `http://localhost:${KUMASCRIPT_PORT}${uri}`;
}

function readTestFixture(relpath) {
    var fullpath = path.join(FIXTURES_PATH, relpath);
    return fs.readFileSync(fullpath, 'utf8').trim();
}

async function testRequest(options) {
    return new Promise((resolve, reject) => {
        request(options, function(err, resp, result) {
            if (!err) {
                resolve([resp, result]);
            } else {
                reject(err);
            }
        });
    });
}

describe('test-server', function() {
    beforeEach(() => {
        // Build both a kumascript instance and a document server for tests.
        this.kuma_server = createKumaServer();
        this.kuma_server.get('/readiness/?', function(req, res) {
            res.sendStatus(204);
        });

        this.server = new Server();
        this.server.listen();
    });

    afterEach(() => {
        // Kill all the servers on teardown.
        this.server.close();
        this.kuma_server.close();
    });

    it('Fetching the root returns the homepage', async () => {
        let [response, result] = await testRequest(getURL('/'));
        expect(result).toEqual(readTestFixture('homepage-expected.html'));
    });

    const documents = ['document1', '시작하기'];
    it.each(documents)('Documents render as expected %s', async filename => {
        let input = readTestFixture(`documents/${filename}.txt`);
        let expected = readTestFixture(`documents/${filename}-expected.txt`);
        let [response, result] = await testRequest({
            method: 'POST',
            url: getURL('/docs/'),
            body: input
        });
        expect(result).toEqual(expected);
    });

    it('Server can handle requests in parallel', async () => {
        const N = 50;
        let input = readTestFixture('documents/document1.txt');
        let expected = readTestFixture('documents/document1-expected.txt');
        let promises = [];
        for (let i = 0; i < N; i++) {
            promises[i] = testRequest({
                method: 'POST',
                url: getURL('/docs/'),
                body: input
            });
        }

        let results = await Promise.all(promises);

        for (let i = 0; i < N; i++) {
            expect(results[i][1]).toEqual(expected);
        }
    });

    it('Variables in request headers are available to templates', async () => {
        function makeHeaders(env) {
            let headers = {};
            for (let [key, value] of Object.entries(env)) {
                headers['x-kumascript-env-' + key] = Buffer.from(
                    JSON.stringify(value),
                    'utf8'
                ).toString('base64');
            }
            return headers;
        }

        let env = {
            locale: 'en-US',
            alpha: 'This is the alpha value',
            beta: 'Consultez les forums dédiés de Mozilla',
            gamma: 'コミュニティ',
            delta: '커뮤니티',
            foo: ['one', 'two', 'three'],
            bar: { a: 1, b: 2, c: 3 }
        };

        let input = readTestFixture('documents/request-variables.txt');
        let expected = readTestFixture(
            'documents/request-variables-expected.txt'
        );

        let [response, result] = await testRequest({
            method: 'POST',
            url: getURL('/docs/'),
            body: input,
            headers: makeHeaders(env)
        });

        expect(result).toEqual(expected);
    });

    it('Macro errors are included in response headers', async () => {
        let input = readTestFixture('documents/document2.txt');
        let expected = readTestFixture('documents/document2-expected.txt');

        let [response, result] = await testRequest({
            method: 'POST',
            url: getURL('/docs/'),
            body: input,
            headers: {
                'X-FireLogger': '1.2'
            }
        });

        expect(result).toBe(expected);
        expect(response.headers.vary).toBe('X-FireLogger');

        let errors = extractErrors(response);

        // TODO: we should modify render.js to produce different
        // errors in each of these three cases
        expect(errors.broken1[0]).toBe('MacroNotFoundError');
        expect(errors.broken2[0]).toBe('MacroCompilationError');
        expect(errors.broken3[0]).toBe('MacroExecutionError');

        expect(errors.broken1[1]).toContain("Unknown macro 'broken1'");
        expect(errors.broken2[1]).toContain("Error compiling macro 'broken2'");
        expect(errors.broken3[1]).toContain("Error rendering macro 'broken3'");

        function extractErrors(resp) {
            // First pass, assemble all the base64 log fragments
            // from headers into buckets by UID.
            let logs_pieces = {};
            for (let [key, value] of Object.entries(resp.headers)) {
                if (key.startsWith('firelogger-')) {
                    let parts = key.split('-');
                    let uid = parts[1];
                    let seq = parts[2];
                    if (!(uid in logs_pieces)) {
                        logs_pieces[uid] = [];
                    }
                    logs_pieces[uid][seq] = value;
                }
            }

            // Second pass, decode the base64 log fragments in each bucket.
            let logs = {};
            for (let [uid, pieces] of Object.entries(logs_pieces)) {
                let json = Buffer.from(pieces.join(''), 'base64').toString(
                    'utf-8'
                );
                logs[uid] = JSON.parse(json).logs;
            }

            // Third pass, extract all kumascript error messages.
            let errors = {};
            for (let [uid, messages] of Object.entries(logs)) {
                for (let m of messages) {
                    if (
                        m.name == 'kumascript' &&
                        m.level == 'error' &&
                        m.args[2] &&
                        m.args[2].name
                    ) {
                        errors[m.args[2].name] = m.args.slice(0, 2);
                    }
                }
            }

            return errors;
        }
    });

    it('Fetching /macros returns macro details', async () => {
        let [response, result] = await testRequest(getURL('/macros'));
        let expected = readTestFixture('macros-expected.json');
        expect(JSON.parse(result)).toEqual(JSON.parse(expected));
    });

    it('Liveness endpoint returns 204 when live', async () => {
        let [response, result] = await testRequest(getURL('/healthz'));
        expect(response.statusCode).toBe(204);
    });

    it('Readiness endpoint returns 204 when ready', async () => {
        let [response, result] = await testRequest(getURL('/readiness'));
        expect(response.statusCode).toBe(204);
    });

    it('Readiness endpoint returns 503 when Kuma is down', async () => {
        this.kuma_server.close();
        let [response, result] = await testRequest(getURL('/readiness'));
        expect(response.statusCode).toBe(503);
        expect(result).toContain('Kuma not ready');
    });

    it('Readiness endpoint returns 503 when kuma not ready', async () => {
        this.kuma_server.close();
        this.kuma_server = createKumaServer();
        this.kuma_server.get('/readiness/?', function(req, res) {
            res.status(503).send('service unavailable due to database issue');
        });
        let [response, result] = await testRequest(getURL('/readiness'));

        expect(response.statusCode).toBe(503);
        expect(result).toContain('Kuma not ready');
        expect(result).toContain('service unavailable due to database issue');
    });

    it('Revision endpoint returns git commit hash', async () => {
        process.env.REVISION_HASH = 'DEADBEEF';
        let [response, result] = await testRequest(getURL('/revision'));
        expect(response.statusCode).toBe(200);
        expect(result).toBe(process.env.REVISION_HASH);
        expect(response.headers['content-type']).toBe(
            'text/plain; charset=utf-8'
        );
    });
});
