define(['intern/dojo/Promise', 'base/lib/config'], function(Promise, config) {

    return {
        until: function(item, fn, callbackFn) {
            // Allows us to poll for a remote.{whatever}() method async result
            // Useful when waiting for an element to fade in, a URL to change, etc.

            // Defaults for arguments not passed
            callbackFn = callbackFn || function(result) {
                return result === true;
            };

            var dfd = new Promise.Deferred();
            var endTime = Number(new Date()) + config.testTimeout;

            (function poll() {
                item[fn]().then(function() {
                    if(callbackFn.apply(this, arguments)) {
                        dfd.resolve();
                    }
                    else if (Number(new Date()) < endTime) {
                        setTimeout(poll, 100);
                    }
                    else {
                        dfd.reject(new Error('timed out for ' + fn + ': ' + item));
                    }
                });
            })();

            return dfd.promise;
        },

        untilUrlChanges: function(remote, desired) {
            // Shortcut method for polling until a URL changes
            // Mostly needed for Chrome

            return this.until(remote, 'getCurrentUrl', function(url) {
                return url.indexOf(desired) != -1;
            });
        },

        untilPopupWindowReady: function(remote, desired) {
            // Shortcut method for polling until a popup window has launched
            // Mostly needed for Chrome

            return this.until(remote, 'getAllWindowHandles', function(handles) {
                return handles.length === (desired || 2);
            });
        }

    };

});
