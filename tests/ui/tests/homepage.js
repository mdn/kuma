define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/poll',
    'base/lib/POM',
    'intern/dojo/node!leadfoot/keys'
], function(registerSuite, assert, config, poll, POM, keys) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
        searchBoxId: 'home-q'
    });


    // Register the tests to be run
    registerSuite({

        name: 'home',

        before: function() {
            return Page.init(this.remote, config.homepageUrl);
        },

        beforeEach: function() {
            return Page.setup();
        },

        after: function() {
            return Page.teardown();
        },

        'Homepage search form displays and accepts text, [ENTER] key submits form': function() {

            var term = 'Hello';

            return this.remote
                        .findById(Page.searchBoxId)
                        .click()
                        .type(term)
                        .getProperty('value')
                        .then(function(resultText) {
                            assert.ok(resultText.indexOf(term) > -1, term + ' is found in box');
                        })
                        .type(keys.RETURN)
                        .getCurrentUrl()
                        .then(function(url) {
                            assert.isTrue(url.indexOf('/search') != -1);
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
                            assert.ok(arr.length > 0, 'If this fails, you may need to upload featured demos via the demo studio to ensure this works');
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
                        .findById(Page.searchBoxId)
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isFalse(bool);
                            // Cleanup the window sizing
                            return remote.setWindowSize(windowSize.width, windowSize.height);
                        });

        },

    });

});
