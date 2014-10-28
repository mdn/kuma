define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/utils',
    'base/lib/credentials'
], function(registerSuite, assert, config, utils, realCredentials) {

    registerSuite({

        name: 'wiki',

        before: function() {
            return utils.completePersonaLogin(this.remote, realCredentials.personaUsername, realCredentials.personaPassword);
        },

        'The new document screen passes all the checks': function() {

            var remote = this.remote;

            return remote.get(config.url + 'docs/new')
                        .then(function() {
                            // Ensure that CKEditor loaded properly
                            return utils.assertWindowPropertyExists(remote, 'CKEDITOR')
                                        // Ensure the tagit plugin is loaded for dynamic tag creation
                                        .then(function() { return utils.assertWindowPropertyExists(remote, 'jQuery.fn.tagit'); })
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
                        .sleep(100000)
                        .then(function() {
                            // Ensure that CKEditor loaded properly
                            return utils.assertWindowPropertyExists(remote, 'ace_editor');
                        });

        }
        */

        after: function() {
            return utils.completePersonaLogout(this.remote);
        }

    });

});
