define([
    'intern!object',
    'intern/chai!assert',
    'base/_config',
    'base/_credentials',
    'base/_utils'
], function(registerSuite, assert, config, realCredentials, utils) {

    registerSuite({

        name: 'auth',

        beforeEach: function() {

            return this.remote
                        .get(config.homepageUrl)
                        .findByCssSelector('.oauth-login-options')
                        .moveMouseTo(5, 5)
                        .end()
                        .findByCssSelector('.oauth-login-picker')
                        .then(function(element) {
                            return utils.pollForRemote(element, 'isDisplayed');
                        });
        },

        'Hovering over the header nav widget opens submenu': utils.checkExistsAndDisplayed('.oauth-login-picker'),

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

            utils.getTestPersonaLoginCredentials(function(credentials) {
                return utils.completePersonaLogin(credentials.email, credentials.password, remote, function() {
                    return remote
                        .then(function() {
                                remote
                                    .getCurrentUrl()
                                    .then(function(url) {
                                        assert.isTrue(url.indexOf('/account/signup') != -1);
                                        return utils.completePersonaLogout(remote).sleep(4000).then(dfd.callback(function() {
                                            return true;
                                        }));
                                    });
                        });
                });

            });

            return dfd;
        },

        'Logging in with Persona with real credentials works': function() {

            var dfd = this.async(config.testTimeout);
            var remote = this.remote;

            utils.completePersonaLogin(realCredentials.personaUsername, realCredentials.personaPassword, remote, function() {

                return remote
                    .findByCssSelector('.user-state-profile')
                    .then(function(element) {
                        utils.pollForRemote(element, 'isDisplayed')
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
                    })

            });

            return dfd;
        },

        'Clicking on the GitHub icon initializes GitHub login process': function() {

            return this.remote
                        .findByCssSelector('.oauth-login-picker a[data-service="GitHub"]')
                        .click()
                        .getCurrentUrl()
                        .then(function(url) {
                            assert.ok(url.toLowerCase().indexOf('github.com') != -1, 'Clicking GitHub login link goes to GitHub.com');
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
