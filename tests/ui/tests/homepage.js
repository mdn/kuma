define([
    'intern!object',
    'intern/chai!assert',
    'base/_config'
], function(registerSuite, assert, config) {

    registerSuite({

        name: 'home',

        beforeEach: function() {
            return this.remote.get(config.homepageUrl);
        },

        'Ensure homepage is displaying search form and accepts text': function() {

            var term = 'Hello';

            return this.remote
                        .findById('home-q')
                        .click()
                        .type(term)
                        .getProperty('value')
                        .then(function(resultText) {
                            assert.ok(resultText.indexOf(term) > -1, term + ' is found in box');
                        });
        },

        'Demo slider displays properly': function() {

            return this.remote
                        .findAllByCssSelector('.owl-item')
                        .then(function(arr) {
                            assert.isTrue(arr.length > 0);
                        });

        },

        'Large search field does not display on mobile and lower': function() {
            // Starting with a "getWindowSize" to do cleanup on this test's resize to mobile

            var remote = this.remote;
            var windowSize;

            return remote
                        .getWindowSize()
                        .then(function(size) {
                            windowSize = size;
                        })
                        .end()
                        .setWindowSize(config.mediaQueries.mobile, 400)
                        .findById('home-q')
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isFalse(bool);

                            // Cleanup the window sizing
                            return remote.setWindowSize(windowSize.width, windowSize.height);
                        });

        }

    });

});
