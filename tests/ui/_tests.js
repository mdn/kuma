define({

    // Non-functional test suite(s) to run in each browser (unit tests)
    suites: [],

    // Functional test suite(s) to run in each browser once non-functional tests are completed
    functionalSuites: [
        'tests/auth',
        'tests/demos',
        'tests/env',
        'tests/footer',
        'tests/header',
        'tests/homepage',
        'tests/wiki'
    ]

});
