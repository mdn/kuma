define([
    'intern!object',
    'intern/chai!assert',
    'base/_config'
], function(registerSuite, assert, config) {

    var testObject = {
        name: 'env',

        before: function() {
            return this.remote.get(config.homepageUrl);
        }
    };

    // window-based objects we rely on for all MDN functionality
    var requiredObjects = [
        'jQuery',
        'mdn',
        'waffle',
        'gettext',
        'Tabzilla'
    ];

    requiredObjects.forEach(function(variable) {
        testObject[variable + ' object is provided to MDN'] = function() {
            this.remote.execute('return typeof window.' + variable + ' != "undefined"').then(function(result) {
                assert.isTrue(result);
            })
        };
    });

    registerSuite(testObject);

});
