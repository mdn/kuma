define([
    'intern!object',
    'intern/chai!assert',
    'intern/dojo/node!leadfoot/keys',
    'base/lib/config',
    'base/lib/login',
    'base/lib/assert',
    'base/lib/poll'
], function(registerSuite, assert, keys, config, libLogin, libAssert, poll) {

    registerSuite({

        name: 'home',

        beforeEach: function() {
            return this.remote.get(config.homepageUrl);
        },

        'Homepage search form displays and accepts text': function() {

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

        'Hacks posts display properly': function() {

            return this.remote
                        .findAllByCssSelector('.home-hacks .entry-title')
                        .then(function(arr) {
                            assert.ok(arr.length > 0, 'If this fails, Hacks posts are not displaying on the homepage');
                        });

        },

        'Demo slider displays properly': function() {

            return this.remote
                        .findAllByCssSelector('.owl-item')
                        .then(function(arr) {
                            assert.ok(arr.length > 0, 'If this fails, you may need to upload demos via the demo studio to ensure this works');
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
                        .setWindowSize(config.mediaQueries.mobile, 400)
                        .findById('home-q')
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isFalse(bool);
                            // Cleanup the window sizing
                            return remote.setWindowSize(windowSize.width, windowSize.height);
                        });

        },

    });

});
