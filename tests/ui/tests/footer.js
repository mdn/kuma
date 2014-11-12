define([
    'intern!object',
    'intern/chai!assert',
    'intern/dojo/node!leadfoot/keys',
    'base/lib/config',
    'base/lib/assert'
], function(registerSuite, assert, keys, config, libAssert) {

    registerSuite({

        name: 'footer',

        beforeEach: function() {
            return this.remote.get(config.homepageUrl);
        },

        'Changing the footer\'s language selector changes locale via URL': function() {

            return this.remote
                        .findById('language')
                        .moveMouseTo(5, 5)
                        .click()
                        .type(['e', keys.RETURN])
                        .getCurrentUrl()
                        .then(function(url) {
                            assert.isTrue(url.indexOf('/es/') != -1);
                        })
                        .goBack(); // Cleanup to go back to default locale
        }

    });

});
