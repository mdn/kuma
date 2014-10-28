define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/utils'
], function(registerSuite, assert, config, utils) {

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
            return utils.assertWindowPropertyExists(this.remote, property);
        };
    });

    registerSuite(testObject);

});
