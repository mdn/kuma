define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/utils'
], function(registerSuite, assert, config, utils) {

    registerSuite({

        name: 'demos',

        before: function() {
            return this.remote.get(config.demosHomepageUrl);
        },

        'The featured demo widget is present': utils.assertExistsAndDisplayed('#demo-main'),

        'The demo search form is present': utils.assertExistsAndDisplayed('#search-demos')

    });

});
