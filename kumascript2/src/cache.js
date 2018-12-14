/**
 * This module defines a cache() function for caching the strings returned by
 * other functions.
 *
 * KumaScript macros originally used memcached for caching. This
 * module is a new backend to replace memcached. Currently it just use
 * a LRU cache in local instance memory, which means that if we have
 * more than one server running KumaScript each will have an
 * independent cache. The cache() function is async, and if necessary,
 * it could be rewritten to use redis instead.
 *
 * @prettier
 */
const LRU = require('lru-cache');
const config = require('./config.js');

const lru = new LRU({
    max: 1024 * 1024 * config.cacheMegabytes,
    maxAge: 60000 * config.cacheMinutes,
    // The size of each cache entry is the length of the key (in characters)
    // plus the length of the value buffer (in bytes), and this is
    // approximately the total size in bytes.
    length: (v, k) => {
        return k.length + v.length;
    }
});

/**
 * Look up the specified key in the cache, and return its value if
 * we have one. Otherwise, call the computeValue() function to compute
 * the value, store it in the cache, and return the value. If skipCache
 * is true, skip the initial cache query and always re-compute the value.
 *
 * Note that computeValue() is expected to be an async function, and
 * we await its result. The result is that this function is async even
 * though the current LRU-based cache is not itself async.
 */
async function cache(key, computeValue, skipCache = false) {
    if (!skipCache) {
        let cached = lru.get(key);
        if (cached !== undefined) {
            if (cached instanceof Buffer) {
                return cached.toString();
            } else {
                // If the cached value is not a buffer, then it is probably
                // null, which is what usually happens if there was an error
                // computing the value
                return cached;
            }
        }
    }

    let value = await computeValue();
    if (typeof value === 'string') {
        lru.set(key, Buffer.from(value));
    } else if (value === null) {
        // The legacy computeValue() functions we're using in environment.js
        // don't have a way to report async errors and typically just report
        // a value of null if anything goes wrong. We're going to go ahead
        // and cache that error value since we don't want to keep computing
        // the same null value over and over.
        lru.set(key, value);
    } else {
        throw new TypeError('cached functions should return string values');
    }

    return value;
}

module.exports = cache;
