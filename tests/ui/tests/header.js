define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/poll',
    'base/lib/POM'
], function(registerSuite, assert, config, libAssert, poll, POM) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
    });

    registerSuite({

        name: 'header',

        before: function() {
            return Page.init(this.remote, config.homepageUrl);
        },

        beforeEach: function() {
            return Page.setup();
        },

        after: function() {
            return Page.teardown();
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

        'The header search box expands and contracts correctly': function() {

            var searchBoxId = 'main-q';
            var homeSearchBoxId = 'home-q';
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
                            })
                            .end()
                            .findById(homeSearchBoxId)
                            .click()
                            .end()
                            .sleep(2000) // wait for animation
                            .findById(searchBoxId)
                            .getSize()
                            .then(function(newSize) {
                                assert.equal(newSize.width, originalSize.width);
                            });
        },

        'Tabzilla loads properly': libAssert.elementExistsAndDisplayed('#tabzilla')

    });

});
