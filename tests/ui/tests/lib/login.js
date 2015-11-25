define([
    'intern/dojo/node!http',
    'intern/dojo/Promise',
    'base/lib/config',
    'base/lib/poll',
    'base/lib/capabilities',
    'intern/dojo/node!leadfoot/helpers/pollUntil',
    'intern/chai!assert',
], function(http, Promise, config, poll, capabilities, pollUntil, assert) {

    return {

        // Login credentials from the command line
        personaUsername: config.personaUsername,
        personaPassword: config.personaPassword,

        openLoginWidget: function(remote) {
            // Simply hovers over the top login widget so that login links can be clicked

            return remote
                    .findByCssSelector('.oauth-login-options')
                    .moveMouseTo(5, 5)
                    .end()
                    .findByCssSelector('.oauth-login-picker')
                    .then(function(element) {
                        return poll.until(element, 'isDisplayed');
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

            var self = this;
            username = username || this.personaUsername;
            password = password || this.personaPassword;

            return remote
                    .then(function() {
                        return self.pollForPersonaLoaded(remote);
                    })
                    .findByCssSelector('.oauth-login-picker .launch-persona-login')
                    .click()
                    .end()
                    .then(function() {
                        return poll.untilPopupWindowReady(remote);
                    })
                    .getAllWindowHandles()
                    .then(function(handles) {

                        return remote.switchToWindow(handles[1])

                            // FOR SAFARI Added this for Safari -- it isn't finding the #authentication_email without it
                            // Safari has a history with popup issues
                            // https://code.google.com/p/selenium/issues/detail?id=5195
                            .sleep(capabilities.getBrowserSleepShim(remote))

                            .findByCssSelector('#authentication_email')
                            .then(function() {

                                // Needing do perform this "hack" instead of polling for element isDisplayed()
                                // due to either a selenium issue or weird construction of Persona window
                                // return poll.until(element, 'isDisplayed')
                                return remote.executeAsync(function(username, done) {

                                    // If the Persona window pitches the "recently signed in accounts" list,
                                    // click "this is not me" to get red of it and start the real login process
                                    var notMeInterval = setInterval(function() {
                                        var notMeButtons = document.querySelector('.thisIsNotMe');
                                        if(notMeButtons) {
                                            notMeButtons.click();
                                            clearInterval(notMeInterval);
                                        }
                                    }, 100);

                                    // Delete some nodes that could get in our way (overlays)
                                    ['load', 'wait', 'error', 'delay'].forEach(function(id) {
                                        var node = document.querySelector('#' + id);
                                        node.parentNode.removeChild(node);
                                    });

                                    // Provide the email address via JS, more reliable than selenium's click()
                                    var interval = setInterval(function() {
                                        var emailField = document.querySelector('#authentication_email');
                                        var isStartButton = document.querySelector('button.isStart');

                                        if(emailField.offsetHeight) {
                                            emailField.value = username;
                                            clearInterval(interval);

                                            // Delay to let the button enable itself `button.isStart`

                                            interval = setInterval(function() {
                                                if(isStartButton.offsetHeight && !isStartButton.disabled) {
                                                    clearInterval(interval);
                                                    done();
                                                }
                                            }, 200);
                                        }
                                    }, 100);
                                }, [username]);
                            })
                            .end()
                            .findByCssSelector('button.isStart')
                            .then(capabilities.crossbrowserConfirm(remote))
                            .end()
                            .findByCssSelector('#authentication_password')
                            .then(function() {

                                // Needing do perform this "hack" instead of polling for element isDisplayed()
                                // due to either a selenium issue or weird construction of Persona window
                                // return poll.until(element, 'isDisplayed')
                                return remote.executeAsync(function(password, done) {

                                    // Provide the password via JS, more reliable than selenium's click()
                                    var interval = setInterval(function() {
                                        var passworldField = document.querySelector('#authentication_password');

                                        if(passworldField.offsetHeight) {
                                            passworldField.value = password;
                                            clearInterval(interval);

                                            var button = document.querySelector('button.isTransitionToSecondary');
                                            if(button.offsetHeight) {
                                                button.focus();
                                                done();
                                            }
                                        }
                                    }, 200);
                                }, [password]);
                            })
                            .end()
                            .findByCssSelector('button.isTransitionToSecondary')
                            .then(capabilities.crossbrowserConfirm(remote))
                            .switchToWindow(handles[0])

                            // A bit crazy, but since we need to wait for Persona to (1) close the login window and
                            // (2) refresh the main window, we need to listen for "beforeunload" to confirm the page is "turning"...
                            .then(function() {

                                return remote.executeAsync(function(done) {
                                    var eventType = 'beforeunload';
                                    var asyncCallback = function() {
                                        window.removeEventListener(eventType, asyncCallback);
                                        done();
                                    };
                                    var listener = window.addEventListener(eventType, asyncCallback);
                                });
                            })

                            .sleep(capabilities.getBrowserSleepShim(remote))

                            // ... and to confirm the login worked, we need to poll for either the "#id_username" element (signup page)
                            // or the "a.oauth-logged-in-signout" element (sign out link)
                            .then(function() {
                                return pollUntil('return document.querySelector("#id_username") || document.querySelector("a.oauth-logged-in-signout")');
                            })

                            .end()
                            .then(callback);
                });
        },

        completePersonaLogin: function(remote, username, password) {
            // Opens the login widget, completes the personal login, done

            var dfd = new Promise.Deferred();
            var self = this;

            username = username || this.personaUsername;
            password = password || this.personaPassword;

            this.openLoginWidget(remote).then(function() {
                self.completePersonaWindow(remote, username, password, dfd.resolve);
            });

            return dfd.promise;
        },

        completePersonaLogout: function(remote) {
            // Completes a "hard" logout of Persona via persona.org
            return remote
                    .findAllByCssSelector('.oauth-logged-in-signout')
                    .then(function(elements) {
                        if(elements.length) {
                            return elements[0].click();
                        }
                        else {
                            return remote.get('https://login.persona.org/')
                                    .findByCssSelector('a.signOut')
                                    .click().end();
                        }
                    });
        },

        pollForPersonaLoaded: function(remote) {
            return remote.executeAsync(function(done) {
                var interval = setInterval(function() {
                    if(document.querySelector('.wait-for-persona.disabled') === null) {
                        done();
                        clearInterval(interval);
                    }
                }, 200);
            });
        }
    };

});
