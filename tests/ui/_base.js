// Learn more about configuring this file at <https://github.com/theintern/intern/wiki/Configuring-Intern>.
// These default settings work OK for most people. The options that *must* be changed below are the
// packages, suites, excludeInstrumentation, and (if you want functional tests) functionalSuites.
define(['./_tests'], function(tests) {

    return {
        // Non-functional test suite(s) to run in each browser
        suites: tests.suites,

        // Functional test suite(s) to run in each browser once non-functional tests are completed
        functionalSuites: tests.functionalSuites,

        // Maximum number of simultaneous integration tests that should be executed on the remote WebDriver service
        maxConcurrency: 1,

        // Configuration options for the module loader; any AMD configuration options supported by the specified AMD loader
        // can be used here
        loaderOptions: {
            // Packages that should be registered with the loader in each testing environment
            packages: [
                { name: 'base', location: './tests' }
            ]
        },

        // A regular expression matching URLs to files that should not be included in code coverage analysis
        excludeInstrumentation: /^(?:.\/*.js|node_modules)\//,

        // Output formatter
        reporters: ['Pretty']
    };

});
