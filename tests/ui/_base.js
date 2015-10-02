// Learn more about configuring this file at <https://github.com/theintern/intern/wiki/Configuring-Intern>.
define({

    // Non-functional test suite(s) to run in each browser (unit tests)
    suites: [],

    // Functional test suite(s) to run in each browser once non-functional tests are completed
    functionalSuites: [
        'tests/header',
        'tests/demos',
        'tests/env',
        'tests/footer',
        'tests/homepage',
        'tests/auth',
        'tests/wiki',
        'tests/dashboards'
    ],

    // Browsers to run integration testing against.
    environments: [],

    // Maximum number of simultaneous integration tests that should be executed on the remote WebDriver service
    maxConcurrency: 1,

    // Name of the tunnel class to use for WebDriver tests
    tunnel: 'NullTunnel',

    // Configuration options for the module loader
    loaderOptions: {
        // Packages that should be registered with the loader in each testing environment
        packages: [
            { name: 'base', location: './tests' }
        ]
    },

    // A regular expression matching URLs to files that should not be included in code coverage analysis
    excludeInstrumentation: /^(_cli\.js|node_modules|tests\/lib)/

});
