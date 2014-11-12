define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/poll'
], function(registerSuite, assert, config, libAssert, poll) {

    registerSuite({

        name: 'header',

        beforeEach: function() {
            return this.remote.get(config.homepageUrl);
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

        'Tabzilla loads properly': libAssert.elementExistsAndDisplayed('#tabzilla')

    });

});
