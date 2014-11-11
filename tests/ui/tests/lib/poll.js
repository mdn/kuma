define(['intern/dojo/Deferred', 'base/lib/config'], function(Deferred, config) {

    return {
        until: function(item, fn, callbackFn, timeout) {
            // Allows us to poll for a remote.{whatever}() method async result
            // Useful when waiting for an element to fade in, a URL to change, etc.

            // Defaults for arguments not passed
            timeout = timeout || config.testTimeout;
            callbackFn = callbackFn || function(result) {
                return result === true;
            };

            var dfd = new Deferred();
            var endTime = Number(new Date()) + timeout;

            (function poll() {
                item[fn]().then(function() {

                    if(callbackFn.apply(this, arguments)) {
                        dfd.resolve();
                    }
                    else if (Number(new Date()) < endTime) {
                        setTimeout(poll, 100);
                    }
                    else {
                        dfd.reject(new Error('timed out for ' + fn + ': ' + arguments));
                    }
                });
            })();

            return dfd.promise;
        }
    };

});
