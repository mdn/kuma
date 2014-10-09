define([
    'intern!object',
    'intern/chai!assert',
    'base/_config',
    'base/_utils'
], function(registerSuite, assert, config, utils) {

    registerSuite({

        name: 'experimental',


        'test polling': function() {
            return this.remote
                    .get(config.homepageUrl)
                    .findByCssSelector('.oauth-login-options')
                    .moveMouseTo(5, 5)
                    .end()
                    .findByCssSelector('.oauth-login-picker')
                    .then(function(element) {
                        return utils.pollForRemote(element, 'isDisplayed').then(function() {
                            assert.isTrue(true);
                        });
                    });
        }


    });
});
