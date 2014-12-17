define([
    'intern!object',
    'intern/chai!assert',
    'intern/dojo/node!leadfoot/keys',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/POM'
], function(registerSuite, assert, keys, config, libAssert, POM) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
    });

    registerSuite({

        name: 'footer',

        before: function() {
            return Page.init(this.remote, config.homepageUrl);
        },

        beforeEach: function() {
            return Page.setup();
        },

        after: function() {
            return Page.teardown();
        },

        'Changing the footer\'s language selector changes locale via URL': function() {

            return this.remote
                        .findById('language')
                        .moveMouseTo(5, 5)
                        .click()
                        .type(['e', keys.RETURN])
                        .getCurrentUrl()
                        .then(function(url) {
                            assert.ok(url.indexOf('/es/') != -1, 'The URL after language selector changed in the footer is: ' + url);
                        })
                        .goBack(); // Cleanup to go back to default locale
        }

    });

});
