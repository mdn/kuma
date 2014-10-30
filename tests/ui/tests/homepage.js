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

        'Hovering over Zones menu displays submenu': function() {

            return this.remote
                        .findByCssSelector('#main-nav a')
                        .moveMouseTo(5, 5)
                        .end()
                        .findById('nav-zones-submenu')
                        .then(function(element) {
                            return poll.until(element, 'isDisplayed').then(function() {
                                // Polling proves it's true :)
                                assert.isTrue(true);
                            });
                        });

        },

        'Focusing on the header search box expands the input': function() {

            var searchBoxId = 'main-q';
            var originalSize;

            return this.remote
                            .findById(searchBoxId)
                            .getSize()
                            .then(function(size) {
                                originalSize = size;
                            })
                            .click()
                            .end()
                            .sleep(2000) // wait for animation
                            .findById(searchBoxId)
                            .getSize()
                            .then(function(newSize) {
                                assert.isTrue(newSize.width > originalSize.width);
                            });
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

        },

        'Tabzilla loads properly': libAssert.elementExistsAndDisplayed('#tabzilla')

    });

});
