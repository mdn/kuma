define([
    'intern!object',
    'base/lib/config',
    'base/lib/assert'
], function(registerSuite, config, libAssert) {

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

    requiredObjects.forEach(function(property) {
        testObject[property + ' object is provided to MDN'] = function() {
            return libAssert.windowPropertyExists(this.remote, property);
        };
    });

    registerSuite(testObject);

});
