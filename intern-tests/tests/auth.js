define([
    'intern!object',
    'intern/chai!assert',
    'base/_config',
    'base/_utils'
], function(registerSuite, assert, config, utils) {

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

        'Hovering over the header nav widget opens submenu': function() {
            return this.remote
                        .findByCssSelector('.oauth-login-picker')
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isTrue(bool);
                        });

        },

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
                utils.completePersonaLogin(credentials.email, credentials.password, remote, function() {
                    return remote
                        .then(function() {
                                remote
                                    .getCurrentUrl()
                                    .then(dfd.callback(function(url) {
                                        assert.isTrue(url.indexOf('/account/signup') != -1);
                                    }));
                        });
                });

            });

            return dfd;
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
                                    .then(dfd.callback(function(url) {
                                        assert.isTrue(url.indexOf('/account/signup') != -1);
                                    }));
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
