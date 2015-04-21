define([
    'intern/dojo/node!http',
    'intern/dojo/Deferred',
    'base/lib/config',
    'base/lib/poll',
    'intern/dojo/node!leadfoot/helpers/pollUntil',
    'intern/chai!assert'
], function(http, Deferred, config, poll, pollUntil, assert) {

    return {

        // Login credentials from the command line
        personaUsername: config.personaUsername,
        personaPassword: config.personaPassword,

        openLoginWidget: function(remote) {
            // Simply hovers over the top login widget so that login links can be clicked

            return remote
                        .get(config.homepageUrl)
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

            username = username || this.personaUsername;
            password = password || this.personaPassword;

            return remote
                        .findByCssSelector('.oauth-login-picker .launch-persona-login')
                        .click()
                        .end()
                        .getAllWindowHandles()
                        .then(function(handles) {
                            return remote.switchToWindow(handles[1])
                                .findById('authentication_email')
                                .click()
                                .type(username)
                                .end()
                                .findByCssSelector('button.isStart')
                                .click()
                                .end()
                                .findById('authentication_password')
                                .then(function() {

                                    // Needing do perform this "hack" instead of polling for element isDisplayed()
                                    // due to either a selenium issue or weird construction of Persona window
                                    // return poll.until(element, 'isDisplayed')
                                    return remote.executeAsync(function(done) {
                                        var interval = setInterval(function() {
                                            if(document.getElementById('authentication_password').offsetHeight) {
                                                clearInterval(interval);
                                                done();
                                            }
                                        }, 200);
                                    });
                                })
                                .click()
                                .type(password)
                                .end()
                                .findByCssSelector('button.isTransitionToSecondary')
                                .click()
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

                                // ... and to confirm the login worked, we need to poll for either the "#id_username" element (signup page)
                                // or the "a.user-state-signout" element (sign out link)
                                .then(function() {
                                    return pollUntil('alert(document.querySelector("#id_username") || document.querySelector("a.user-state-signout")); return document.querySelector("#id_username") || document.querySelector("a.user-state-signout")');
                                })

                                .end()
                                .then(callback);
                    });
        },

        completePersonaLogin: function(remote, username, password) {
            // Opens the login widget, completes the personal login, done

            var dfd = new Deferred();
            var self = this;

            username = username || this.personaUsername;
            password = password || this.personaPassword;

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
        }
    };

});
