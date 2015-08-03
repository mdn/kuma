define([
    'intern!object',
    'intern/chai!assert',
    'intern/dojo/node!leadfoot/keys',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/POM',
    'base/lib/poll'
], function(registerSuite, assert, keys, config, libAssert, POM, poll) {

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

            var remote = this.remote;

            return remote
                        .findByCssSelector('#language')
                        .moveMouseTo(5, 5)
                        .click()
                        .type(['e', keys.RETURN])
                        .then(function() {
                            return poll.untilUrlChanges(remote, '/es/').then(function() {
                                assert.isTrue(true, 'Locale auto-redirects');
                            });
                        })
                        .goBack(); // Cleanup to go back to default locale
        }

    });

});
