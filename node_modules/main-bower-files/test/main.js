var mainBowerFiles = require('../'),
    path = require('path');

require('should');

describe('main-bower-files', function() {
    function expect(filenames) {
        var expectedFiles = [].concat(filenames).map(function(filename) {
            return path.join(__dirname, filename);
        });

        function run(path, options, done) {
            options = options || {};

            var srcFiles,
                filter = options.filter || undefined;

            if (!options.paths) {
                options.paths = {};
            }

            if (!options.paths.bowerJson) {
                options.paths.bowerJson = __dirname + path;
            }

            if (!options.paths.bowerrc) {
                options.paths.bowerrc = __dirname + '/.bowerrc';
            }

            if (typeof filter === 'string' || Array.isArray(filter)) {
                delete options.filter;
                srcFiles = mainBowerFiles(filter, options);
            } else {
                srcFiles = mainBowerFiles(options);
            }

            srcFiles.should.be.eql(expectedFiles);

            if (done) {
                done();
            }
        }

        return {
            fromConfig: function(path, options) {
                return {
                    when: function(done) {
                        run(path, options, done);
                    }
                };
            }
        };
    }

    it('should select the expected files', function(done) {
        expect([
            '/fixtures/simple/simple.js',
            '/fixtures/overwritten/another.js',
            '/fixtures/multi/multi.js',
            '/fixtures/multi/multi.css',
            '/fixtures/hasPackageNoBower/hasPackageNoBower.js',
            '/fixtures/deepPaths/lib/deeppaths.js',
            '/fixtures/decoy/decoy.js'
        ]).fromConfig('/_bower.json').when(done);
    });

    it('should select only files that pass a given filter regular expression', function(done) {
        expect([
            '/fixtures/simple/simple.js',
            '/fixtures/overwritten/another.js',
            '/fixtures/multi/multi.js',
            '/fixtures/hasPackageNoBower/hasPackageNoBower.js',
            '/fixtures/deepPaths/lib/deeppaths.js',
            '/fixtures/decoy/decoy.js'
        ]).fromConfig('/_bower.json', { filter: /\.js$/i }).when(done);
    });

    it('should select only files that pass a given glob filter', function(done) {
        expect([
            '/fixtures/simple/simple.js',
            '/fixtures/overwritten/another.js',
            '/fixtures/multi/multi.js',
            '/fixtures/hasPackageNoBower/hasPackageNoBower.js',
            '/fixtures/deepPaths/lib/deeppaths.js',
            '/fixtures/decoy/decoy.js'
        ]).fromConfig('/_bower.json', { filter: '**/*.js' }).when(done);
    });

    it('should select only files that pass a given filter callback', function(done) {
        expect([
            '/fixtures/decoy/decoy.js'
        ]).fromConfig('/_bower.json', {
            filter: function(file) {
                return file.indexOf('decoy.js') > -1;
            }
        }).when(done);
    });

    it('should select the expected files with relative path', function(done) {
        expect([
            '/fixtures/simple/simple.js',
            '/fixtures/overwritten/another.js',
            '/fixtures/multi/multi.js',
            '/fixtures/multi/multi.css',
            '/fixtures/hasPackageNoBower/hasPackageNoBower.js',
            '/fixtures/deepPaths/lib/deeppaths.js',
            '/fixtures/decoy/decoy.js'
        ]).fromConfig('/_bower.json', {
            paths: {
                bowerJson: './test/_bower.json',
                bowerDirectory: './test/fixtures'
            }
        }).when(done);
    });

    it('should ignore packages without any json files', function(done) {
        expect([
            '/fixtures/simple/simple.js'
        ]).fromConfig('/_nojson_bower.json').when(done);
    });

    it('should select files via default option', function(done) {
        expect([
            '/fixtures/noconfig/noconfig.js',
            '/fixtures/simple/simple.js'
        ]).fromConfig('/_nojson_bower.json', { main: './**/*.js' }).when(done);
    });

    it('should recurse through dependencies pulling in their dependencies', function(done) {
        expect([
            '/fixtures/simple/simple.js',
            '/fixtures/recursive/recursive.js'
        ]).fromConfig('/_recursive_bower.json').when(done);
    });

    it('should not get hungup on cyclic dependencies', function(done) {
        expect([
            '/fixtures/cyclic-a/cyclic-a.js',
            '/fixtures/cyclic-b/cyclic-b.js'
        ]).fromConfig('/_cyclic_bower.json').when(done);
    });

    it('should get devDependencies', function(done) {
        expect([
            '/fixtures/simple/simple.js',
            '/fixtures/includeDev/includeDev.js'
        ]).fromConfig('/_includedev_bower.json', { includeDev: true }).when(done);
    });

    it('should get only devDependencies', function(done) {
        expect([
            '/fixtures/includeDev/includeDev.js'
        ]).fromConfig('/_includedev_bower.json', { includeDev: 'exclusive' }).when(done);
    });

    it('should get devDependencies and ignore missing dependencies', function(done) {
        expect([
            '/fixtures/includeDev/includeDev.js'
        ]).fromConfig('/_includedev_devdepsonly_bower.json', { includeDev: true }).when(done);
    });

    it('should get main file', function(done) {
        expect([
            'main.js'
        ]).fromConfig('/_includeSelf_bower.json', { includeSelf: true }).when(done);
    });

    it('should not load any deeper dependencies', function(done) {
        expect([
            '/fixtures/recursive/recursive.js'
        ]).fromConfig('/_dependencies_bower.json').when(done);
    });

    it('should load other dependencies than defined', function(done) {
        expect([
            '/fixtures/decoy/decoy.js',
            '/fixtures/recursive/recursive.js'
        ]).fromConfig('/_other_dependencies_bower.json').when(done);
    });

    it('should select prod.js on prod environment', function(done) {
        process.env.NODE_ENV = 'prod';
        expect([
            '/fixtures/envBased/prod.js'
        ]).fromConfig('/_env_based_bower.json').when(done);
    });

    it('should select dev.js on dev environment', function(done) {
        process.env.NODE_ENV = 'dev';
        expect([
            '/fixtures/envBased/dev.js'
        ]).fromConfig('/_env_based_bower.json').when(done);
    });

    it('should ignore missing main file if checkExistence is false', function() {
        var when = expect([]).fromConfig('/_not_existing_file.json').when;

        when.should.not.throw();
    });

    it('should not ignore missing main file if checkExistence is true', function() {
        var when = expect([]).fromConfig('/_not_existing_file.json', { checkExistence: true }).when;

        when.should.throw();
    });

    it('should ignore missing main property if checkExistence is false', function() {
        var when = expect([]).fromConfig('/_not_existing_main.json').when;

        when.should.not.throw();
    });

    it('should not ignore missing main property if checkExistence is true', function() {
        var when = expect([]).fromConfig('/_not_existing_main.json', { checkExistence: true }).when;

        when.should.throw();
    });

    it('should not throw an exception if there are no packages', function() {
        var when = expect([]).fromConfig('/_empty.json').when;

        when.should.not.throw();
    });

    it('should throw an exception if bower.json does not exists', function() {
        var when = expect([]).fromConfig('/_unknown.json').when;

        when.should.throw();
    });

    it('should not throw an exception if bowerrc has no directory property defined', function() {
        var when = expect([]).fromConfig('/_empty.json', {
            paths: {
                bowerDirectory: __dirname + '/fixtures',
                bowerrc: __dirname + '/.bowerrc_without_directory'
            }
        }).when;

        when.should.not.throw();
    });

    it('should select the expected files with comments in the bower.json', function(done) {
        expect([
            '/fixtures/overwritten/another.js'
        ]).fromConfig('/_bower_with_comments.json').when(done);
    });
});
