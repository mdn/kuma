define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/login',
    'base/lib/assert',
    'base/lib/poll',
    'base/lib/POM',
    'base/lib/capabilities'
], function(registerSuite, assert, config, libLogin, libAssert, poll, POM, capabilities) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
    });

    registerSuite({

        name: 'auth',

        before: function() {
            Page.init(this.remote, config.homepageUrl);
        },

        beforeEach: function() {
            return Page.setup().then(function() {
                return libLogin.openLoginWidget(Page.remote);
            });
        },

        after: function() {
            return Page.teardown();
        },

        'Hovering over the header nav widget opens submenu': libAssert.elementExistsAndDisplayed('.oauth-login-picker'),

        'Clicking Persona link opens new window': function() {

            var remote = this.remote;

            return remote
                    .then(function() {
                        return libLogin.pollForPersonaLoaded(remote);
                    })
                    .findByCssSelector('.oauth-login-picker .launch-persona-login')
                    .click()
                    .then(function() {
                        return poll.untilPopupWindowReady(remote);
                    })
                    .end()
                    .getAllWindowHandles()
                    .then(function(handles) {
                        assert.equal(handles.length, 2, 'There are two windows upon Persona click');
                    });

        },

        'Logging in with Persona for the first time sends user to registration page': function() {

            var dfd = this.async(config.testTimeout);
            var remote = this.remote;

            libLogin.getTestPersonaLoginCredentials(function(credentials) {
                return libLogin.completePersonaWindow(remote, credentials.email, credentials.password).then(function() {
                    return poll.untilUrlChanges(remote, '/account/signup').then(function() {
                        assert.ok('User sent to registration page');
                        return libLogin.completePersonaLogout(remote).then(dfd.resolve);
                    });
                });
            });

            return dfd;
        },

        '[requires-login] Logging in with Persona with real credentials works': function() {

            var dfd = this.async(config.testTimeout);
            var remote = this.remote;

            libLogin.completePersonaWindow(remote).then(function() {

                return remote
                        .findByCssSelector('.oauth-logged-in-user')
                        .then(function(element) {
                            return poll.until(element, 'isDisplayed')
                                    .then(function() {
                                        return element
                                                .click()
                                                .then(function() {
                                                     return poll.untilUrlChanges(remote, '/profiles');
                                                })
                                                .then(function() {
                                                    return remote
                                                            .findByCssSelector('#edit-user')
                                                            .click()
                                                            .end()
                                                            .then(function() {
                                                                 return poll.untilUrlChanges(remote, '/edit');
                                                            })
                                                            .findByCssSelector('.submission button[type=submit]')
                                                            .click()
                                                            .end()
                                                            .then(function() {
                                                                 return poll.untilUrlChanges(remote, '/profiles');
                                                            })
                                                            .sleep(capabilities.getBrowserSleepShim(remote))
                                                            .findByCssSelector('.oauth-logged-in-signout')
                                                            .click()
                                                            .end()
                                                            .sleep(capabilities.getBrowserSleepShim(remote))
                                                            .then(dfd.callback(function() {
                                                                assert.ok('User can sign out without problems');
                                                            }));
                                                });
                                    });
                        });

            });

            return dfd;
        },

        'Clicking on the GitHub icon initializes GitHub login process': function() {

            var remote = this.remote;

            // Safari hangs on this test because we cross domains to GitHub.com
            // Unfortunately Safari has history issues
            //
            // From the Safari Selenium extension:
            // "Yikes! Safari history navigation does not work.
            // We can go forward or back, but once we do, we can no longer communicate
            // with the page... (WARNING: The server did not provide any stacktrace information)"
            if(capabilities.getBrowserName(remote) === 'safari') {
                return remote;
            }

            return remote
                    .findByCssSelector('.oauth-login-picker a[data-service="GitHub"]')
                    .click()
                    .then(function() {
                        return poll.untilUrlChanges(remote, 'github.com').then(function() {
                            assert.ok('User sent to GitHub.com');
                        });
                    });
        },

        'Sign in icons are hidden from header widget on smaller screens': function() {

            return this.remote
                        .setWindowSize(config.mediaQueries.tablet, 400)
                        .findByCssSelector('.oauth-login-options .oauth-icon')
                        .moveMouseTo(5, 5)
                        .isDisplayed()
                        .then(assert.isFalse);
        }
    });

});
