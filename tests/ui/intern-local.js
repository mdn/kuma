// Learn more about configuring this file at <https://github.com/theintern/intern/wiki/Configuring-Intern>.
// These default settings work OK for most people. The options that *must* be changed below are the
// packages, suites, excludeInstrumentation, and (if you want functional tests) functionalSuites.
define(['./_base', './_cli', 'intern'], function(config, cli, intern) {

    // Browsers to run integration testing against.
    config.environments = [
        { browserName: 'firefox' },
        { browserName: 'chrome' },
        { browserName: 'safari' }
    ];

    config.tunnelOptions = {
        hostname: '127.0.0.1',
        port: 4444
    };

    return cli.mixinArgs(intern.args, config);
});
