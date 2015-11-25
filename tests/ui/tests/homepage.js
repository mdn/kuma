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

            var remote = this.remote;
            var term = 'Hello';

            return remote
                    .findByCssSelector('#' + Page.searchBoxId)
                    .click()
                    .type(term)
                    .getProperty('value')
                    .then(function(resultText) {
                        assert.ok(resultText.indexOf(term) > -1, term + ' is found in box');
                    })
                    .type(keys.RETURN)
                    .then(function() {
                        return poll.untilUrlChanges(remote, '/search').then(function() {
                            assert.ok('Pressing [ENTER] submits search');
                        });
                    });
        },

        'Hacks posts display properly': function() {

            return this.remote
                        .findAllByCssSelector('.home-hacks .entry-title')
                        .then(function(arr) {
                            assert.ok(arr.length, 'If this fails, Hacks posts are not displaying on the homepage');
                        });

        },

        'Large search field does not display on mobile and lower': function() {
            // Starting with a "getWindowSize" to do cleanup on this test's resize to mobile

            return this.remote
                        .setWindowSize(config.mediaQueries.mobile, 400)
                        .findByCssSelector('#' + Page.searchBoxId)
                        .isDisplayed()
                        .then(assert.isFalse);

        },

    });

});
