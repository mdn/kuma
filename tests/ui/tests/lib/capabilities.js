define(['intern/dojo/node!leadfoot/keys'], function(keys) {

    return {

        getBrowserName: function(remote) {
            // Returns the browser of the current session

            return remote.session.capabilities.browserName.toLowerCase();
        },

        getBrowserSleepShim: function(remote) {
            // Safari and Chrome are whack with popups and crossing domains so we need to shim it with sleeps;
            // Polling for elements is not fruitful, so simply waiting is the best solution

            return 3000;
        },

        crossbrowserConfirm: function(remote) {
            // Firefox and Chrome react more reliably to elements with the ENTER key pressed
            // Safari, on the other hand, only responds to click

            var gbn = this.getBrowserName(remote);

            return function(element) {
                if(gbn === 'safari') {
                    return element.click();
                }
                else {
                    return element.type([keys.RETURN]);
                }
            };
        }

    };

});
