define([
    'intern!object',
    'intern/chai!assert',
    'base/_config'
], function(registerSuite, assert, config) {

    registerSuite({

        name: 'demos',

        before: function() {
            return this.remote.get(config.demosHomepageUrl);
        },

        'The featured demo widget works correctly': function() {

            return this.remote
                        .findById('demo-main')
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isTrue(bool);
                        });

        },

        'The demo search form is present': function() {

            return this.remote
                        .findbyId('search-demos')
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isTrue(bool);
                        });

        }

    });

});
