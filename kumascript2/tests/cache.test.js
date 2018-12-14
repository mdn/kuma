/**
 * Test the cache() function. Note, however, that we do not attempt to
 * test the timeout and the LRU features of the underlying node-lru cache.
 *
 * @prettier
 */
const cache = require('../src/cache.js');

describe('cache() function', () => {
    it('does basic caching', async () => {
        let compute = jest.fn(() => String(Math.random()));

        let value1 = await cache('key1', compute);
        let value2 = await cache('key2', compute);
        expect(compute.mock.calls.length).toBe(2);

        // Subsequent calls return the cached values
        // and do not invoke the compute() function.
        expect(await cache('key1', compute)).toBe(value1);
        expect(await cache('key2', compute)).toBe(value2);
        expect(compute.mock.calls.length).toBe(2);
    });

    it('we can bypass cache with skipCache=true', async () => {
        let compute = jest.fn(() => String(Math.random()));

        let value1 = await cache('key3', compute);
        expect(compute.mock.calls.length).toBe(1);

        let value3 = await cache('key3', compute, true);
        expect(compute.mock.calls.length).toBe(2);
    });
});
