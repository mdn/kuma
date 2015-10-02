// Learn more about configuring this file at <https://github.com/theintern/intern/wiki/Configuring-Intern>.
// These default settings work OK for most people. The options that *must* be changed below are the
// packages, suites, excludeInstrumentation, and (if you want functional tests) functionalSuites.
define(['./_base', './_cli', 'intern'], function(config, cli, intern) {

    // Browsers to run integration testing against. Note that version numbers must be strings if used with Sauce
    // OnDemand. Options that will be permutated are browserName, version, platform, and platformVersion; any other
    // capabilities options specified for an environment will be copied as-is
    config.environments = [
        { browserName: 'internet explorer', version: '11', platform: ['Windows 7', 'Windows 8.1', 'Windows 10'] },
        { browserName: 'firefox', version: ['40', '39', '38'], platform: [ 'OS X 10.9', 'OS X 10.10', 'Windows 7', 'Windows 8.1', 'Windows 10', 'Linux' ] },
        { browserName: 'chrome', version: ['44', '45'], platform: [ 'OS X 10.9', 'OS X 10.10', 'Windows 7', 'Windows 8.1', 'Windows 10', 'Linux' ] },
        { browserName: 'safari', version: ['9', '8'], platform: ['OS X 10.9', 'OS X 10.10'] }
    ];

    // Name of the tunnel class to use for WebDriver tests
    config.tunnel = 'SauceLabsTunnel';

    // Format for outputting test results
    config.reporters = ['Pretty'];

    return cli.mixinArgs(intern.args, config);
});
