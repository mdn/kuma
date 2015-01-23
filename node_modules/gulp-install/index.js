'use strict';
var through2 = require('through2'),
    gutil = require('gulp-util'),
    path = require('path'),
    commandRunner = require('./lib/' + (isTest() ? 'test_' : '') + 'commandRunner'),
    cmdMap = {
      'bower.json': {cmd: 'bower', args: ['install', '--config.interactive=false']},
      'package.json': {cmd: 'npm', args: ['install']}
    };

module.exports = exports = function install (opts) {
  var toRun = [],
      count = 0;

  return through2(
    {objectMode: true},
    function (file, enc, cb) {
      if (!file.path) {
        cb();
      }
      var cmd = clone(cmdMap[path.basename(file.path)]);

      if (cmd) {
        if(opts && opts.production) {
          cmd.args.push('--production');
        }

        cmd.cwd = path.dirname(file.path);
        toRun.push(cmd);
      }
      this.push(file);
      cb();
    },
    function (cb) {
      if (!toRun.length) {
        return cb();
      }
      if (skipInstall()) {
        log('Skipping install.', 'Run `' + gutil.colors.yellow(formatCommands(toRun)) + '` manually');
        return cb();
      } else {
        toRun.forEach(function (command) {
          commandRunner.run(command, function (err) {
            if (err) {
              log(err.message, 'Run `' + gutil.colors.yellow(formatCommand(command)) + '` manually');
            }
            done(cb, toRun.length);
          });
        });
      }
    }
  );

  function done (cb, length) {
    if (++count === length) {
      cb();
    }
  }
};

function log () {
  if (isTest()) {
    return;
  }
  gutil.log.apply(gutil, [].slice.call(arguments));
}

function formatCommands (cmds) {
  return cmds.map(formatCommand).join(' && ');
}

function formatCommand (command) {
  return command.cmd + ' ' + command.args.join(' ');
}

function skipInstall () {
  return process.argv.slice(2).indexOf('--skip-install') >= 0;
}

function isTest () {
  return process.env.NODE_ENV === 'test';
}

function clone (obj) {
  if (Array.isArray(obj)) {
    return obj.map(clone);
  } else if (typeof obj === 'object') {
    var copy = {};
    Object.keys(obj).forEach(function (key) {
      copy[key] = clone(obj[key]);
    });
    return copy;
  } else {
    return obj;
  }
}
