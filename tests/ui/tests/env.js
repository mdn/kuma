define([
    'intern!object',
    'intern/chai!assert',
    'base/_config',
    'base/_utils'
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
            return utils.checkWindowPropertyExists(this.remote, property);
        };
    });

    registerSuite(testObject);

});
