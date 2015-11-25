define([
    'intern!object',
    'intern/chai!assert',
    'base/lib/config',
    'base/lib/assert',
    'base/lib/POM',
    'base/lib/poll',
    'base/lib/capabilities',
    'intern/dojo/text!tests/fixtures/in-content.html'
], function(registerSuite, assert, config, libAssert, POM, poll, capabilities, inContentTemplate) {

    // Create this page's specific POM
    var Page = new POM({
        // Any functions used multiple times or important properties of the page
        documentCreatedSlug: ''
    });

    function confirmCKEditorReady(remote) {
        return remote.executeAsync(function(done) {
            var checkInterval = setInterval(function() {
                var ck = window.CKEDITOR;
                if(ck && ck.instances.id_content && ck.instances.id_content.status === 'ready') {
                    clearInterval(checkInterval);
                    done();
                }
            }, 200);
        });
    }

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
                                    return remote
                                            .findByCssSelector('#id_title')
                                            .click()
                                            .type('Hello$ World')
                                            .end()
                                            .findByCssSelector('#id_slug')
                                            .getSpecAttribute('value').then(function(value) {
                                                    assert.ok(value === 'Hello__World', 'The slugify function is working properly');
                                            });
                                });
                    });
        },

        '[requires-login] IFRAME elements are not allowed by CKEditor': function() {

            var remote = this.remote;


            return remote.get(config.url + 'docs/new')
                    .then(function() {
                        return confirmCKEditorReady(remote);
                    })
                    .then(function() {
                        // Go into source mode, add an IFRAME, go back into view mode, ensure iframe isn't there
                        return remote.executeAsync(function(done) {
                            var editor = CKEDITOR.instances.id_content;
                            var interval, html;

                            editor.on('mode', function() {
                                if(editor.mode == 'source') {
                                    document.querySelector('.cke_source').value = '<p>Hi!</p><iframe src="http://davidwalsh.name"></iframe><img src="javascript:;" onerror="alert(1);">';
                                }
                                else {
                                    html = editor.getData().toLowerCase();
                                    done(html.indexOf('<iframe') === -1 && html.indexOf('onerror') === -1);
                                    clearInterval(interval);
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
                    .findByCssSelector('#edit-button')
                    .moveMouseTo(5, 5)
                    .click()
                    .then(function() {
                        return poll.untilUrlChanges(remote, '$edit').then(function() {
                            assert.ok('Clicking edit button loads edit page');
                        });
                    })
                    .then(function() {
                        return confirmCKEditorReady(remote);
                    });
        },

        '[requires-login][requires-doc] Clicking the "translate button" allows for translation and CKEditor loads': function() {

            var remote = this.remote;

            return remote.get(config.url + 'docs/' + config.wikiDocumentSlug)
                    .findByCssSelector('#languages-menu')
                    .moveMouseTo(5, 5)
                    .end()
                    .findByCssSelector('#languages-menu-submenu')
                    .then(function(element) {
                        return poll.until(element, 'isDisplayed').then(function() {
                            return remote.findByCssSelector('#translations-add')
                                    .click()
                                    .then(function() {
                                        return poll.untilUrlChanges(remote, '$locales').then(function() {
                                            assert.ok('Clicking edit button loads edit page');
                                        });
                                    })
                                    .end()
                                    .findByCssSelector('.locales a')
                                    .click()
                                    .end()
                                    .then(function() {
                                        return poll.untilUrlChanges(remote, '$translate').then(function() {
                                            assert.ok('Clicking translate link loads translate page');
                                        });
                                    })
                                    .then(function() {
                                        return confirmCKEditorReady(remote);
                                    });
                        });
                    });
        },

        '[requires-login][requires-destructive] Can create a document, button becomes enabled as soon as updates made': function() {

            var remote = this.remote;
            var title = 'Intern Test ' + new Date().getTime();

            return remote.get(config.url + 'docs/new')
                    .then(function() {
                        return confirmCKEditorReady(remote);
                    })
                    .then(function() {
                            return remote
                                    .findByCssSelector('#id_title')
                                    .click()
                                    .type(title)
                                    .end()
                                    .findByCssSelector('#id_slug')
                                    .getSpecAttribute('value')
                                    .then(function(value) {
                                        Page.documentCreatedSlug = value;

                                        return remote.executeAsync(function(html, done) {
                                                var interval = setInterval(function() {
                                                    CKEDITOR.instances.id_content.setData(html);
                                                    clearInterval(interval);
                                                    done();
                                                }, 200);
                                            }, [inContentTemplate])
                                            .then(function() {

                                                return remote
                                                        .findByCssSelector('.page-buttons .btn-save')
                                                        .then(capabilities.crossbrowserConfirm(remote))
                                                        .then(function() {
                                                            return poll.untilUrlChanges(remote, Page.documentCreatedSlug).then(function() {
                                                                assert.ok('New page is created successfully');
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
                        scrollTo(0, 1200);
                        setTimeout(done, 1000);
                    })
                    .end()
                    .findByCssSelector(tocSelector)
                    .getComputedStyle('top')
                    .then(function(y) {
                        assert.isTrue(y == '0' || y == '0px', 'Testing y value: ' + y);
                    })
                    .getComputedStyle('position')
                    .then(function(position) {
                        assert.isTrue(position === 'fixed', 'Testing position is fixed: ' + position);
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
