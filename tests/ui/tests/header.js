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
            // Possible ToDo:  Move click() call after the transitionend event listener

            var remote = this.remote;
            var searchBoxId = 'main-q';
            var homeSearchBoxId = 'home-q';
            var originalWidth;

            var transitionEndCallback = function() {
                return remote.executeAsync(function(done) {
                    var element = document.getElementById('main-q');
                    var eventType = 'transitionend';

                    var ev = element.addEventListener(eventType, function(){
                        element.removeEventListener(eventType, ev);
                        done();
                    });
                });
            }

            return remote
                            .findById(searchBoxId)
                            .getSize()
                            .then(function(size) {
                                originalWidth = size.width;
                            })
                            .click() // ToDo:  Will calling click first cause a timing issue?
                            .then(transitionEndCallback)
                            .findById(searchBoxId)
                            .getSize()
                            .then(function(newSize) {
                                assert.isTrue(newSize.width > originalWidth);
                            })
                            .end()
                            .then(function() {
                                return remote
                                            .findById(homeSearchBoxId)
                                            .click() // ToDo:  Will calling click first cause a timing issue?
                                            .end()
                                            .then(transitionEndCallback)
                                            .findById(searchBoxId)
                                            .getSize()
                                            .then(function(newSize) {
                                                assert.equal(newSize.width, originalWidth);
                                            });
                            });

        },

        'Tabzilla loads properly': libAssert.elementExistsAndDisplayed('#tabzilla')

    });

});
