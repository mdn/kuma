var path                = require('path'),
    fs                  = require('fs'),
    stripJsonComments   = require('strip-json-comments'),
    Package             = require('./package'),
    logger              = require('./logger'),
    PackageCollection;

/**
 * Collection for bower packages
 *
 * @class PackageCollection
 */

/**
 * @constructor
 * @param {Object} opts
 */
PackageCollection = function(opts) {
    this.opts               = opts;
    this.opts.main          = opts.main || null;
    this.opts.env           = opts.env || process.env.NODE_ENV;
    this.debugging          = opts.debugging || false;
    this.overrides          = {};
    this._queue             = [];
    this._lastQueueLength   = 0;
    this._packages          = {};
    this._processed         = {};

    this.collectPackages();
};

PackageCollection.prototype = {
    /**
     * Adds a package to the collection
     *
     * @param {String} name Name of the package
     * @param {String} path Path to the package files
     */
    add: function(name, path) {
        if (typeof this._packages[name] !== 'undefined') {
            return;
        }

        if (this.debugging) {
            logger('PackageCollection', 'add\t\t', name, path);
        }

        this._packages[name] = true;

        var opts = this.overrides[name] || {};
        opts.name = name;
        opts.path = path;
        if (path.indexOf(this.opts.paths.bowerDirectory) === -1) {
            opts.main = name;
        }
        opts.path = path;

        this._packages[name] = new Package(opts, this);
    },

    /**
     * Collects all packages
     */
    collectPackages: function() {
        if (!fs.existsSync(this.opts.paths.bowerJson)) {
            throw new Error('bower.json does not exist at: ' + this.opts.paths.bowerJson);
        }

        var name,
            includeDev = this.opts.includeDev || false,
            includeSelf = this.opts.includeSelf || false,
            bowerJson = JSON.parse(
                stripJsonComments(
                    fs.readFileSync(this.opts.paths.bowerJson, 'utf8')
                )
            ),
            devDependencies = bowerJson.devDependencies || {},
            dependencies = bowerJson.dependencies || {},
            main = bowerJson.main || {};

        includeDev = includeDev === true ? 'inclusive' : includeDev;

        this.overrides = bowerJson.overrides || {};

        if (includeDev !== 'exclusive') {
            for (name in dependencies) {
                this.add(name, path.join(this.opts.paths.bowerDirectory, path.sep, name));
            }
        }

        if (includeDev !== false) {
            for (name in devDependencies) {
                this.add(name, path.join(this.opts.paths.bowerDirectory, path.sep, name));
            }
        }

        if (includeSelf !== false) {
            this.add(main, path.join(path.dirname(this.opts.paths.bowerJson)));
        }
    },

    /**
     * Get srcs of all packages
     *
     * @return {Array}
     */
    getFiles: function() {
        for (var name in this._packages) {
            this._queue.push(this._packages[name]);
        }

        return this.process();
    },

    /**
     * processes the queue and returns the srcs of all packages
     *
     * @private
     * @return {Array}
     */
    process: function() {
        var queue = this._queue,
            srcs = [],
            force = false;

        if (this._lastQueueLength === queue.length) {
            force = true;
        }

        this._lastQueueLength = queue.length;

        this._queue = [];

        queue.forEach(function(package) {
            var packageSrcs = package.getFiles(force);

            if (packageSrcs === false) {
                return this._queue.push(package);
            }

            srcs.push.apply(srcs, packageSrcs);
            this._processed[package.name] = true;
        }.bind(this));

        if (this._queue.length) {
            srcs.push.apply(srcs, this.process());
        }

        return srcs;
    }
};

module.exports = PackageCollection;
