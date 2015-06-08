define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/POM',
    'base/lib/poll',
    'intern/dojo/node!leadfoot/keys',
    'intern/dojo/text!tests/fixtures/in-content.html'
], function(registerSuite, assert, config, libAssert, POM, poll, keys, inContentTemplate) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
        documentCreatedSlug: ''
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

        '[requires-login] IFRAME elements are not allowed by CKEditor': function() {

            var remote = this.remote;

            return remote.get(config.url + 'docs/new')
                        .then(function() {
                            // Go into source mode, add an IFRAME, go back into view mode, ensure iframe isn't there
                            return remote.executeAsync(function(done) {
                                var editor = CKEDITOR.instances.id_content;
                                var interval;

                                editor.on('mode', function() {
                                    if(editor.mode == 'source') {
                                        document.querySelector('.cke_source').value = '<p>Hi!</p><iframe src="http://davidwalsh.name"></iframe><img src="javascript:;" onerror="alert(1);">';
                                    }
                                    else {
                                        clearInterval(interval);

                                        var html = editor.getData().toLowerCase();
                                        done(html.indexOf('<iframe') === -1 && html.indexOf('onerror') === -1);
                                    }
                                });

                                interval = setInterval(function() {
                                    editor.execCommand('source');
                                }, 300);
                            })
                            .then(assert.isTrue);
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
        },

        '[requires-login][requires-destructive] Can create a document, button becomes enabled as soon as updates made': function() {

            var remote = this.remote;
            var title = 'Intern Test ' + new Date().getTime();

            return remote.get(config.url + 'docs/new')
                        .then(function() {
                                return remote.findById('id_title').click().type(title).then(function() {
                                    return remote.findById('id_slug').getSpecAttribute('value').then(function(value) {
                                        Page.documentCreatedSlug = value;

                                        return remote.executeAsync(function(html, done) {
                                                            if(window.CKEDITOR) {
                                                                CKEDITOR.instances.id_content.setData(html);
                                                                done();
                                                            }
                                                    }, [inContentTemplate])
                                                    .then(function() {

                                                        return remote.findAllByCssSelector('.page-buttons .btn-save')
                                                                .type([keys.RETURN])
                                                                .getCurrentUrl()
                                                                .then(function(url) {
                                                                    assert.isTrue(url.indexOf(Page.documentCreatedSlug) != -1);
                                                                });
                                                    });



                                    });
                                });
                        });

        },

        // Ensures the TOC scrolls down with the user
        '[requires-login][requires-destructive] Created page passes TOC tests': function() {

            var remote = this.remote;
            var tocSelector = '#toc';

            return remote.get(config.url + '/docs/' + Page.documentCreatedSlug)
                        .then(function() {
                            return libAssert.elementExistsAndDisplayed(tocSelector);
                        })
                        .executeAsync(function(done) {
                            scrollTo(0, 600);
                            done();
                        })
                        .end()
                        .findByCssSelector(tocSelector)
                        .getComputedStyle('top')
                        .then(function(y) {
                            assert.isTrue(y == '0' || y == '0px');
                        })
                        .getComputedStyle('position')
                        .then(function(position) {
                            assert.isTrue(position == 'fixed');
                        });

        },

        // Ensure the review popups display by default
        '[requires-login][requires-destructive] Created page displays review requests': function() {

            return this.remote.get(config.url + '/docs/' + Page.documentCreatedSlug)
                        .then(function() {
                            return libAssert.elementExistsAndDisplayed('.page-meta.reviews');
                        });

        }

    });

});
