const request = require('supertest');
const app = require('./ssr-server.js');

// This is a fake ssr() functiona
function mockssr(name, data) {
    return `<${name} ${JSON.stringify(data)}>`;
}
// We're mocking the ssr module with the mock function
jest.mock('./dist/ssr.js', () => mockssr);

describe('ssr-server routes', () => {
    it('get /', () =>
        request(app)
            .get('/')
            .expect(200)
            .expect('Content-Type', 'text/html; charset=utf-8')
            .then(response => {
                expect(response.text).toContain('SSR server ready');
            }));

    it.each(['/healthz', '/healthz/', '/readiness', '/readiness/'])(
        'get %s returns 204',
        path =>
            request(app)
                .get(path)
                .expect(204)
    );

    it.each([['/revision', 'foo'], ['/revision/', 'bar']])(
        'get %s returns revision',
        (path, revision) => {
            process.env.REVISION_HASH = revision;
            return request(app)
                .get(path)
                .expect(200)
                .expect(response => {
                    expect(response.text).toBe(revision);
                });
        }
    );

    it.each(['/ssr', '/ssr/'])('GET %s returns 404', path =>
        request(app)
            .get(path)
            .expect(404)
    );

    it.each(['foo', 'bar'])('POST /ssr/%s calls ssr()', name => {
        const data = { foo: 1 };
        return request(app)
            .post(`/ssr/${name}`)
            .send(data)
            .expect(200)
            .expect('Content-Type', 'application/json; charset=utf-8')
            .expect(response => {
                expect(response.body).toBe(mockssr(name, data));
            });
    });
});
