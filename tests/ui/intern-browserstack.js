// Learn more about configuring this file at <https://github.com/theintern/intern/wiki/Configuring-Intern>.
// These default settings work OK for most people. The options that *must* be changed below are the
// packages, suites, excludeInstrumentation, and (if you want functional tests) functionalSuites.
define(['./_base', './_cli', 'intern'], function(config, cli, intern) {

    // Name of the tunnel class to use for WebDriver tests
    config.tunnel = 'BrowserStackTunnel';

    config.capabilities = {
        'browserstack.ie.noFlash': true,
        'browserstack.ie.enablePopups': true
    };

    // Browsers to run integration testing against.
    config.environments = [
        { browserName: 'firefox', platform: ['MAC', 'WIN8'] },
        { browserName: 'chrome', platform: ['MAC', 'WIN8'] },
        { browserName: 'internet explorer', version: '11', platform: 'WIN8' },
    ];

    // Name of the tunnel class to use for WebDriver tests
    config.tunnel = 'BrowserStackTunnel';

    // Format for outputting test results
    config.reporters = ['Pretty'];

    return cli.mixinArgs(intern.args, config);
});
