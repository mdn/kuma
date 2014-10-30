define([
    'intern',
    'intern/dojo/node!http',
    'intern/dojo/Deferred',
    'base/lib/config',
    'base/lib/poll',
    'intern/chai!assert'
], function(intern, http, Deferred, config, poll, assert) {

    return {

        // Login credentials from the command line
        personaUsername: intern.args.u,
        personaPassword: intern.args.p,

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

                        // Using jQuery's click() method because WebDriver not registering the click on an inline link
                        /*
                        .findByCssSelector('a.signOut')
                        .moveMouseTo(12, 12)
                        .sleep(2000)
                        click();
                        */
        }
    };

});
