define([
    'intern!object',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/POM'
], function(registerSuite, config, libAssert, POM) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
    });

    var testObject = {

        name: 'env',

        before: function() {
            return Page.init(this.remote, config.homepageUrl);
        },

        beforeEach: function() {
            return Page.setup();
        },

        after: function() {
            return Page.teardown();
        },
    };

    // window-based objects we rely on for all MDN functionality
    var requiredObjects = [
        'jQuery',
        'mdn',
        'waffle',
        'gettext'
    ];

    requiredObjects.forEach(function(property) {
        testObject[property + ' object is provided to MDN'] = function() {
            return libAssert.windowPropertyExists(this.remote, property);
        };
    });

    registerSuite(testObject);

});
