define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/POM',
    'base/lib/poll'
], function(registerSuite, assert, config, libAssert, POM, poll) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
    });

    registerSuite({

        name: 'wiki',

        before: function() {
            Page.init(this.remote, config.homepageUrl);
        },

        beforeEach: function() {
            return Page.setup();
        },

        after: function() {
            return Page.teardown();
        },

        '[requires-login] Logging in for wiki tests': function() {
            // This appears here instead of "before" so that login isn't attempted
            // due to '[requires-login]'

            return Page.login();
        },

        '[requires-login] The new document screen passes all the checks': function() {

            var remote = this.remote;

            return remote.get(config.url + 'docs/new')
                        .then(function() {
                            // Ensure that CKEditor loaded properly
                            return libAssert.windowPropertyExists(remote, 'CKEDITOR')
                                        // Ensure the tagit plugin is loaded for dynamic tag creation
                                        .then(function() { return libAssert.windowPropertyExists(remote, 'jQuery.fn.tagit'); })
                                        // Ensure that populating the title populates the slug field correctly
                                        .then(function() {
                                            return remote.findById('id_title').click().type('Hello$ World').then(function() {
                                                return remote.findById('id_slug').getSpecAttribute('value').then(function(value) {
                                                    assert.ok(value === 'Hello__World', 'The slugify function is working properly');
                                                });
                                            });
                                        });
                        });

        },

        '[requires-login] The new document-template screen passes all the checks': function() {

            var remote = this.remote;

            return remote.get(config.url + 'docs/new?slug=Template:')
                        .then(function() {
                            // Ensure that Ace loaded properly
                            return libAssert.windowPropertyExists(remote, 'ace_editor');
                        });

        },

        '[requires-login][requires-doc] Existing document shows "Edit", "Advanced" and "Languages" menu': function() {

            return this.remote.get(config.url + 'docs/' + config.wikiDocumentSlug)
                        .then(function() {
                            return libAssert.elementExistsAndDisplayed('#edit-button');
                        })
                        .then(function() {
                            return libAssert.elementExistsAndDisplayed('#advanced-menu');
                        })
                        .then(function() {
                            return libAssert.elementExistsAndDisplayed('#languages-menu');
                        });

        },

        '[requires-login][requires-doc] Clicking the edit button goes to edit page, CKEditor loads properly': function() {

            var remote = this.remote;

            return remote.get(config.url + 'docs/' + config.wikiDocumentSlug)
                        .findById('edit-button')
                        .moveMouseTo(5, 5)
                        .click()
                        .then(function() {
                            return libAssert.windowPropertyExists(remote, 'CKEDITOR');
                        });
        },

        '[requires-login][requires-doc] Clicking the "translate button" allows for translation and CKEditor loads': function() {

            var remote = this.remote;

            return remote.get(config.url + 'docs/' + config.wikiDocumentSlug)
                        .findById('languages-menu')
                        .moveMouseTo(5, 5)
                        .end()
                        .findById('languages-menu-submenu')
                        .then(function(element) {
                            return poll.until(element, 'isDisplayed').then(function() {
                                return remote.findById('translations-add')
                                    .click()
                                    .end()
                                    .findByCssSelector('.locales a')
                                    .click()
                                    .then(function() {
                                        return libAssert.windowPropertyExists(remote, 'CKEDITOR');
                                    });
                            });
                        });
        }


    });

});
