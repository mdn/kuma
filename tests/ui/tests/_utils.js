define([
    'intern/dojo/node!http',
    'intern/dojo/Deferred',
    'base/_config'
], function(http, Deferred, config) {

    return {

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

        completePersonaLogin: function(username, password, remote, callback) {
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
                                .then(callback);

                    });
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

                    console.log('ping ', arguments[0]);
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
        }
    };

});
