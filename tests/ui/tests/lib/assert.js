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
            // Ensures a window[key] property exists in the page
            // Missing global properties could be a sign of a huge problem

            return remote.execute('return typeof window.' + property + ' != "undefined"').then(function(result) {
                assert.isTrue(result, 'The following window property exists:  ' + property);
            });
        }
    };

});
