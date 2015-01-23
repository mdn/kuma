
var hasRun = [];

exports.commandsThatHasRun = hasRun;

exports.run = function (command, cb) {
  hasRun.push(command);
  cb();
};

exports.reset = function () {
  hasRun.length = 0;
};

