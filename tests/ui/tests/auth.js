define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/login',
    'base/lib/assert',
    'base/lib/poll',
    'base/lib/POM'
], function(registerSuite, assert, config, libLogin, libAssert, poll, POM) {

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
                        .findByCssSelector('.oauth-login-picker .launch-persona-login')
                        .click()
                        .end()
                        .getAllWindowHandles()
                        .then(function(handles) {
                            assert.equal(handles.length, 2);

                            return remote.switchToWindow(handles[1])
                                .getPageTitle()
                                .then(function(title) {
                                    assert.ok(title.toLowerCase().indexOf('persona') != -1, 'Persona window opens upon login click');
                                    return remote.closeCurrentWindow().switchToWindow(handles[0]);
                                });
                        });

        },

        'Logging in with Persona for the first time sends user to registration page': function() {

            var dfd = this.async(config.testTimeout);
            var remote = this.remote;

            libLogin.getTestPersonaLoginCredentials(function(credentials) {
                return libLogin.completePersonaWindow(remote, credentials.email, credentials.password).then(function() {
                    return remote
                        .then(function() {
                                return remote
                                    .getCurrentUrl()
                                    .then(function(url) {
                                        assert.isTrue(url.indexOf('/account/signup') != -1);
                                        return libLogin.completePersonaLogout(remote).then(dfd.resolve);
                                    });
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
                    .findByCssSelector('.user-state-profile')
                    .then(function(element) {
                        poll.until(element, 'isDisplayed')
                                .then(function() {
                                    return element
                                                .click()
                                                .then(function() {
                                                    return remote
                                                                .findById('edit-profile')
                                                                .click()
                                                                .end()
                                                                .findByCssSelector('.fm-submit button[type=submit]')
                                                                .click()
                                                                .end()
                                                                .findByCssSelector('.memberSince')
                                                                .click() // Just ensuring the element is there
                                                                .end()
                                                                .findByCssSelector('.user-state-signout')
                                                                .click()
                                                                .end()
                                                                .findByCssSelector('.oauth-login-container')
                                                                .then(dfd.callback(function() {
                                                                    assert.isTrue(true, 'User can sign out without problems');
                                                                }));
                                                });
                                });
                    });

            });

            return dfd;
        },

        'Clicking on the GitHub icon initializes GitHub login process': function() {

            return this.remote
                        .findByCssSelector('.oauth-login-picker a[data-service="GitHub"]')
                        .click()
                        .getCurrentUrl()
                        .then(function(url) {
                            assert.ok(url.toLowerCase().indexOf('github.com') != -1, 'Clicking GitHub login link goes to GitHub.com. (Requires working GitHub login.)');
                        })
                        .goBack(); // Cleanup to go back to MDN from GitHub sign in page

        },

        'Sign in icons are hidden from header widget on smaller screens': function() {

            return this.remote
                        .setWindowSize(config.mediaQueries.tablet, 400)
                        .findByCssSelector('.oauth-login-options .oauth-icon')
                        .moveMouseTo(5, 5)
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isFalse(bool);
                        });

        }
    });

});
