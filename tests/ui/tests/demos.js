define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/assert'
], function(registerSuite, assert, config, libAssert) {

    registerSuite({

        name: 'demos',

        before: function() {
            return this.remote.get(config.demosHomepageUrl);
        },

        'The featured demo widget is present': libAssert.elementExistsAndDisplayed('#demo-main'),

        'The demo search form is present': libAssert.elementExistsAndDisplayed('#search-demos')

    });

});
