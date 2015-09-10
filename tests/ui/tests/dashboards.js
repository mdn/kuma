define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/login',
    'base/lib/POM',
    'base/lib/poll'
], function(registerSuite, assert, config, libLogin, POM, poll) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
        documentCreatedSlug: ''
    });

    registerSuite({

        name: 'dashboards',

        before: function() {
            Page.init(this.remote, config.url + 'dashboards/revisions');
        },

        beforeEach: function() {
            return Page.setup();
        },

        after: function() {
            return Page.teardown();
        },

        'Revision dashboard renders': function() {

            var remote = this.remote;

            return remote.get(config.url + 'dashboards/revisions').then(function() {
                return remote.findByTagName('h1').getVisibleText().then(function(text) {
                    assert.strictEqual(text, 'Revision Dashboard');
                });
            });
        },

        '[requires-login][requires-destructive] Revision dashboard banning': function() {

            var dfd = this.async(config.testTimeout);
            var remote = this.remote;

            return libLogin.completePersonaWindow(remote).then(function() {
                return remote.get(config.url + 'dashboards/revisions').then(function() {
                    return remote.findById('show_ips_btn').then(function(element) {
                        return element.getVisibleText().then(function(text) {
                            assert.strictEqual(text, 'TOGGLE IPS');

                            return element.click().then(function(element) {
                                return poll.until(element, 'isDisplayed').then(function() {
                                    return remote.findByCssSelector('a.dashboard-ban-ip-link').then(function(element){
                                        return element.click().then(function() {
                                            return remote.getCurrentUrl().then(dfd.callback(function(url) {
                                                assert.isTrue(url.indexOf('ipban/add') != -1);
                                            }));
                                        });
                                    });
                                });
                            });
                        });
                    });
                });
            });
        },
    });
});
