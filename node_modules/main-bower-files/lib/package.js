var path    = require('path'),
    fs      = require('fs'),
    glob    = require('glob'),
    logger  = require('./logger'),
    Package;

/**
 * Holds information of the bower package
 *
 * @class Package
 */

/**
 * @constructor
 * @param {Object}              opts
 * @param {PackageCollection}   collection
 */
Package = function(opts, collection) {
    this.collection     = collection;
    this.name           = opts.name || null;
    this.path           = opts.path || null;
    this.main           = opts.main || null;
    this.dependencies   = opts.dependencies;
    this.ignore         = opts.ignore || false;
    this.debugging      = collection.debugging || false;

    if (this.ignore) {
        return;
    }

    this.collectData();
    this.addDependencies();
};

Package.prototype = {
    /**
     * Collects data from first found config file
     */
    collectData: function() {
        var paths = [
                path.join(this.path, '.bower.json'),
                path.join(this.path, 'bower.json'),
                path.join(this.path, 'package.json'),
                path.join(this.path, 'component.json')
            ],
            data = paths.reduce(function(prev, curr) {
                if (prev !== null && typeof prev.main !== 'undefined') {
                    return prev;
                }

                if (!fs.existsSync(curr)) {
                    return prev;
                }

                try {
                    return JSON.parse(fs.readFileSync(curr, 'utf8'));
                } catch (e) {
                    return null;
                }
            }, null);

        if (data === null) {
            return;
        }

        if (!this.main && data.main) {
            this.main = data.main;

            if (this.debugging) {
                logger('Package\t\t', 'overriding main\t', this.name, data.main);
            }
        }

        if (!this.main && this.collection.opts.checkExistence === true) {
            throw new Error('Main property of package "' + this.name + '" is missing.');
        }

        if (this.dependencies === undefined && data.dependencies && data.dependencies) {
            this.dependencies = data.dependencies;

            if (this.debugging) {
                logger(
                    'Package\t\t',
                    'overriding dependencies\t',
                    this.name,
                    data.dependencies);
            }
        }
    },

    /**
     * Adds package dependencies to the collection
     */
    addDependencies: function() {
        for (var name in this.dependencies) {
            this.collection.add(name, path.join(this.path, '..', name));
        }
    },

    /**
     * Gets main files of the package
     *
     * @param  {Boolean}
     *      force  If true it will not wait for the dependencies
     * @return {Mixed}
     *      Returns false if the package has dependencies which were not
     *      processed yet otherwise an array of file paths
     */
    getFiles: function(force) {
        if (this.ignore) {
            return [];
        }

        if (this.main === null && (this.main = this.collection.opts.main) === null) {
            return [];
        }

        var main = this.main,
            files = [],
            name;

        if (typeof main === 'object' &&
            !Array.isArray(main) &&
            !(main = main[this.collection.opts.env])) {
            return [];
        }

        main = Array.isArray(main) ? main : [main];

        if (force !== true) {
            for (name in this.dependencies) {
                if (this.collection._processed[name] !== true) {
                    return false;
                }
            }
        }

        main.forEach(function(pattern) {
            var _files = glob.sync(pattern, {
                cwd: this.path
            });

            if (!_files.length && this.collection.opts.checkExistence === true) {
                throw new Error('File on path "' + path.join(this.path, pattern) +
                    '" does not exist.');
            }

            _files.forEach(function(file) {
                files.push(path.join(this.path, file));
            }.bind(this));
        }.bind(this));

        if (this.debugging) {
            files.forEach(function(file) {
                logger('Package\t\t', 'select file\t', this.name, file);
            }.bind(this));
        }

        return files;
    }
};

module.exports = Package;
