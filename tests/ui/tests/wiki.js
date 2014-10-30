define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/login',
    'base/lib/assert'
], function(registerSuite, assert, config, libLogin, libAssert) {

    registerSuite({

        name: 'wiki',

        before: function() {
            return libLogin.completePersonaLogin(this.remote);
        },

        'The new document screen passes all the checks': function() {

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
        /*
        'The new document-template screen passes all the checks': function() {

            var remote = this.remote;

            return remote.get(config.url + 'docs/new?slug=Template:')
                        .then(function() {
                            // Ensure that CKEditor loaded properly
                            return libAssert.windowPropertyExists(remote, 'ace_editor');
                        });

        }
        */

        after: function() {
            return libLogin.completePersonaLogout(this.remote);
        }

    });

});
