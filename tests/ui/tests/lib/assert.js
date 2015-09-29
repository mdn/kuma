define(['intern/chai!assert'], function(assert) {
    // Utility functions which end in an assert statement

    return {

        elementExistsAndDisplayed: function(cssSelector) {
            // Shortcut method for ensuring a single element exists and is displaying

            return function() {
                return this.remote
                        .findByCssSelector(cssSelector)
                        .isDisplayed()
                        .then(function(bool) {
                            assert.isTrue(bool, 'The following element is present and displaying: ' + cssSelector);
                        });
            };

        },

        windowPropertyExists: function(remote, property) {
            // Checks the window namespace to ensure a given key is set

            return remote.executeAsync(function(property, done) {
                var interval = setInterval(function() {
                    if(eval('typeof window.' + property + ' != "undefined"')) {
                        clearInterval(interval);
                        done();
                    }
                }, 100);
            }, [property]);

        }
    };

});
