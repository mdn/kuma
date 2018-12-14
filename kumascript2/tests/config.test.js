/**
 * @prettier
 */
describe('config.js', () => {
    beforeEach(() => {
        // We want to reload the config.js module for each test
        jest.resetModules();
    });

    it('default configuration', () => {
        const config = require('../src/config.js');

        expect(config.port).toBe(9080);
        expect(config.documentURLTemplate).toBe(
            'https://developer.mozilla.org/en-US/docs/{path}?raw=1&redirect=no'
        );
        expect(config.documentURL).toBe('https://developer.mozilla.org');
        expect(config.interactiveExamplesURL).toBe(
            'https://interactive-examples.mdn.mozilla.net'
        );
        expect(config.liveSamplesURL).toBe('https://mdn.mozillademos.org');
        expect(config.cacheMegabytes).toBe(50);
        expect(config.cacheMinutes).toBe(60);
        expect(config.envHeaderPrefix).toBe('x-kumascript-env-');
    });

    it('configured with environment variables', () => {
        process.env['KUMASCRIPT_PORT'] = '80';
        process.env['DOCUMENT_URL_TEMPLATE'] = 'A';
        process.env['DOCUMENT_URL'] = 'B';
        process.env['INTERACTIVE_EXAMPLES_URL'] = 'C';
        process.env['LIVE_SAMPLES_URL'] = 'D';
        process.env['KUMASCRIPT_CACHE_MEGABYTES'] = '100';
        process.env['KUMASCRIPT_CACHE_MINUTES'] = '1000';

        const config = require('../src/config.js');

        expect(config.port).toBe(80);
        expect(config.documentURLTemplate).toBe('A');
        expect(config.documentURL).toBe('B');
        expect(config.interactiveExamplesURL).toBe('C');
        expect(config.liveSamplesURL).toBe('D');
        expect(config.cacheMegabytes).toBe(100);
        expect(config.cacheMinutes).toBe(1000);
    });
});
