define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/POM'
], function(registerSuite, assert, config, libAssert, POM) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
    });

    registerSuite({

        name: 'demos',

        before: function() {
            return Page.init(this.remote, config.demosHomepageUrl);
        },

        beforeEach: function() {
            return Page.setup();
        },

        after: function() {
            return Page.teardown();
        },

        'The 3 featured "demos-main" element is present': libAssert.elementExistsAndDisplayed('#demo-main'),

        'The demo search form is present': libAssert.elementExistsAndDisplayed('#search-demos')

    });

});
