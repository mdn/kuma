define([
    'intern!object',
    'intern/chai!assert',
    'base/_config',
    'base/_utils'
], function(registerSuite, assert, config, utils) {

    registerSuite({

        name: 'demos',

        before: function() {
            return this.remote.get(config.demosHomepageUrl);
        },

        'The featured demo widget works correctly': utils.checkExistsAndDisplayed('#demo-main'),

        'The demo search form is present': utils.checkExistsAndDisplayed('#search-demos')

    });

});
