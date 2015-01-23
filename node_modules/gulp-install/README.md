# gulp-install [![NPM version][npm-image]][npm-url] [![Build Status][travis-image]][travis-url] [![Dependency Status][depstat-image]][depstat-url]

> Automatically install npm and bower packages if package.json or bower.json is found in the gulp file stream respectively

## Primary objective

Used as the install step when using [`slush`](https://www.npmjs.org/package/slush) as a Yeoman replacement.

## Installation

### For global use with slush

Install `gulp-install` as a dependency:

```shell
npm install --save gulp-install
```

### For local use with gulp

Install `gulp-install` as a development dependency:

```shell
npm install --save-dev gulp-install
```

## Usage

### In your `slushfile.js`:

```javascript
var install = require("gulp-install");

gulp.src(__dirname + '/templates/**')
  .pipe(gulp.dest('./'))
  .pipe(install());
```

### In your `gulpfile.js`:

```javascript
var install = require("gulp-install");

gulp.src(['./bower.json', './package.json'])
  .pipe(install());
```

## Options

To not trigger the install use `--skip-install` as CLI parameter when running `slush` or `gulp`.

### options.production

**Type:** `Boolean`

**Default:** `false`


Set to `true` if `npm install` should be appended with the `--production` parameter when stream contains `package.json`.

**Example:**

```javascript
var install = require("gulp-install");

gulp.src(__dirname + '/templates/**')
  .pipe(gulp.dest('./'))
  .pipe(install({production: true}));
```

## License

[MIT License](http://en.wikipedia.org/wiki/MIT_License)

[npm-url]: https://npmjs.org/package/gulp-install
[npm-image]: https://badge.fury.io/js/gulp-install.png

[travis-url]: http://travis-ci.org/slushjs/gulp-install
[travis-image]: https://secure.travis-ci.org/slushjs/gulp-install.png?branch=master

[depstat-url]: https://david-dm.org/slushjs/gulp-install
[depstat-image]: https://david-dm.org/slushjs/gulp-install.png
