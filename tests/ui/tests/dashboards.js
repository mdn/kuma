define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/login',
    'base/lib/POM',
    'base/lib/poll',
    'base/lib/capabilities'
], function(registerSuite, assert, config, libLogin, POM, poll, capabilities) {

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

            return this.remote.findByCssSelector('h1').getVisibleText().then(function(text) {
                assert.strictEqual(text, 'Revision Dashboard');
            });
        },

        '[requires-login][requires-destructive] Revision dashboard banning': function() {

            var remote = this.remote;

            return libLogin.openLoginWidget(remote).then(function() {
                return libLogin.completePersonaWindow(remote);
            }).then(function() {
                return remote
                        .findByCssSelector('#show_ips_btn')
                        .click()
                        .end()
                        .findByCssSelector('a.dashboard-ban-ip-link')
                        .click()
                        .end()
                        .then(function() {
                            return poll.untilPopupWindowReady(remote);
                        })
                        .getAllWindowHandles().then(function(handles) {
                            return remote
                                    .switchToWindow(handles[1])
                                    .sleep(capabilities.getBrowserSleepShim(remote))
                                    .getCurrentUrl()
                                    .then(function(url) {
                                        assert.isTrue(url.indexOf('ipban/add') != -1);
                                    });
                        });
                });

        }
    });
});
