define([
    'intern/dojo/node!http',
    'intern/dojo/Deferred',
    'base/lib/config',
    'intern/chai!assert'
], function(http, Deferred, config, assert) {

    return {

        openLoginWidget: function(remote) {
            // Simply hovers over the top login widget so that login links can be clicked

            var pollForRemote = this.pollForRemote;

            return remote
                        .get(config.homepageUrl)
                        .findByCssSelector('.oauth-login-options')
                        .moveMouseTo(5, 5)
                        .end()
                        .findByCssSelector('.oauth-login-picker')
                        .then(function(element) {
                            return pollForRemote(element, 'isDisplayed');
                        });
        },

        getTestPersonaLoginCredentials: function(callback) {
            // Makes a GET request to get a test email address
            // and password for Persona

            return http.get({
                host: 'personatestuser.org',
                path: '/email'
            }, function(response) {
                var body = '';
                response.on('data', function(d) {
                    body += d;
                });
                response.on('end', function() {
                    var parsed = JSON.parse(body);
                    callback({
                        email: parsed.email,
                        password: parsed.pass
                    });
                });
            });

        },

        completePersonaWindow: function(remote, username, password, callback) {
            // Provided a username and passwords, clicks the Persona link in the site
            // header, waits for the window to load, and logs the user into Persona

            var pollForRemote = this.pollForRemote;

            return remote
                        .findByCssSelector('.oauth-login-picker .launch-persona-login')
                        .click()
                        .end()
                        .getAllWindowHandles()
                        .then(function(handles) {
                            return remote.switchToWindow(handles[1])
                                .sleep(2000) // TODO:  Make this programmatic; i.e. an API call to poll when the email field is visible
                                .findById('authentication_email')
                                .click()
                                .type(username)
                                .end()
                                .findByCssSelector('button.isStart')
                                .click()
                                .end()
                                .sleep(2000) // TODO:  Make this programmatic; i.e. an API call to poll when the password field is visible
                                .findById('authentication_password')
                                .click()
                                .type(password)
                                .end()
                                .findByCssSelector('button.isTransitionToSecondary')
                                .click()
                                .switchToWindow(handles[0])
                                .sleep(6000) // TODO:  Make this programmatic; i.e. an API call to poll when first window has loaded new page
                                .end()
                                .then(callback);
                    });
        },

        completePersonaLogin: function(remote, username, password) {
            // Opens the login widget, completes the personal login, done

            var dfd = new Deferred();
            var self = this;

            self.openLoginWidget(remote).then(function() {
                self.completePersonaWindow(remote, username, password, dfd.resolve);
            });

            return dfd.promise;
        },

        completePersonaLogout: function(remote) {
            // Completes a "hard" logout of Persona via persona.org

            return remote
                        .get('https://login.persona.org/')
                        .execute('return jQuery("a.signOut").click();');

                        // Using jQuery's click() method because WebDriver not registering the click on an inline link
                        /*
                        .findByCssSelector('a.signOut')
                        .moveMouseTo(12, 12)
                        .sleep(2000)
                        click();
                        */
        },

        pollForRemote: function(item, remoteFunction, callback, timeout) {
            // Allows us to poll for a remote.{whatever}() method async result
            // Useful when waiting for an element to fade in, a URL to change, etc.

            // Defaults for arguments not passed
            timeout = timeout || config.testTimeout;
            callback = callback || function(result) {
                return result === true;
            };

            var dfd = new Deferred();
            var endTime = Number(new Date()) + timeout;

            (function poll() {
                item[remoteFunction]().then(function() {

                    if(callback.apply(this, arguments)) {
                        dfd.resolve();
                    }
                    else if (Number(new Date()) < endTime) {
                        setTimeout(poll, 100);
                    }
                    else {
                        dfd.reject(new Error('timed out for ' + remoteFunction + ': ' + arguments));
                    }
                });
            })();

            return dfd.promise;
        },

        assertExistsAndDisplayed: function(cssSelector) {
            // Shortcut method for ensuring a single element exists and is displaying

            return function() {
                return this.remote
                        .findByCssSelector(cssSelector)
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isTrue(bool);
                        });
            };

        },

        assertWindowPropertyExists: function(remote, property) {
            // Ensures a window[key] property exists in the page
            // Missing global properties could be a sign of a huge problem

            return remote.execute('return typeof window.' + property + ' != "undefined"').then(function(result) {
                assert.isTrue(result);
            });
        }
    };

});
