define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/poll',
    'base/lib/POM',
    'intern/dojo/node!leadfoot/keys'
], function(registerSuite, assert, config, libAssert, poll, POM, keys) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
    });

    var searchBoxId = 'main-q';

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
                        .findByCssSelector('#nav-platform-submenu')
                        .then(function(element) {
                            return poll.until(element, 'isDisplayed').then(function() {
                                // Polling proves it's true :)
                                assert.ok('Zone submenu is displayed!');
                            });
                        });

        },

        'The header search box expands and contracts correctly': function() {

            var remote = this.remote;
            var originalWidth;

            var transitionEvent = function(done) {
                var element = document.querySelector('#main-q');
                element.addEventListener('transitionend', function(e) {
                    if(e.propertyName === 'width') {
                        element.classList.toggle('boo');
                    }
                });
                done();
            };

            var transitionSniffer = function(hope, done) {
                var interval = setInterval(function() {
                    if(document.querySelector('#main-q').classList.contains('boo') === hope) {
                        clearInterval(interval);
                        done();
                    }
                }, 200);
            };

            return remote
                    .executeAsync(transitionEvent)
                    .findByCssSelector('#' + searchBoxId)
                    .getSize()
                    .then(function(size) {
                        originalWidth = size.width;
                    })
                    .moveMouseTo(5, 5)
                    .click()
                    .end()
                    .executeAsync(transitionSniffer, [true])
                    .findByCssSelector('#' + searchBoxId)
                    .getSize()
                    .then(function(newSize) {
                        assert.isTrue(newSize.width > originalWidth, 'The new width (' + newSize.width + ') is larger than original width (' + originalWidth + ')');
                    })
                    .end()
                    .findByCssSelector('body')
                    .moveMouseTo(5, 5)
                    .click()
                    .end()
                    .executeAsync(transitionSniffer, [false])
                    .findByCssSelector('#' + searchBoxId)
                    .getSize()
                    .then(function(newSize) {
                        assert.equal(newSize.width, originalWidth, 'The new width (' + newSize.width + ') is equal to the original width (' + originalWidth + ')');
                    });
        },

        'Pressing [ENTER] submits the header search box': function() {

            var remote = this.remote;

            return remote
                    .findByCssSelector('#' + searchBoxId)
                    .click()
                    .type(['css', keys.RETURN])
                    .then(function() {
                        return poll.untilUrlChanges(remote, '/search').then(function() {
                            assert.ok('Pressing [ENTER] submits search');
                        });
                    });
        }

    });

});
