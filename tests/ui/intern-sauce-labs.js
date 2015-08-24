// Learn more about configuring this file at <https://github.com/theintern/intern/wiki/Configuring-Intern>.
// These default settings work OK for most people. The options that *must* be changed below are the
// packages, suites, excludeInstrumentation, and (if you want functional tests) functionalSuites.
define(['./_base', './_cli', 'intern'], function(config, cli, intern) {

    // Browsers to run integration testing against. Note that version numbers must be strings if used with Sauce
    // OnDemand. Options that will be permutated are browserName, version, platform, and platformVersion; any other
    // capabilities options specified for an environment will be copied as-is
    config.environments = [
        //{ browserName: 'firefox', version: '40', platform: [ 'OS X 10.9' ] },
        { browserName: 'chrome', version: '43', platform: [ 'OS X 10.9' ] },
        //{ browserName: 'safari', version: '8', platform: 'OS X 10.9' },
        //{ browserName: 'internet explorer', version: '11', platform: 'Windows 8.1' }
    ];

    // Name of the tunnel class to use for WebDriver tests
    config.tunnel = 'SauceLabsTunnel';

    return cli.mixinArgs(intern.args, config);
});
