/*
 * wiki.js
 * Scripts for the wiki app.
 *
 */
(function ($, win, doc) {
    'use strict';

    /*
        Initialization of the CKEditor widget
    */
    (function() {
        var $textarea = $('#id_content');

        // CKEditor setup method
        var setup = function() {
            var $tools = $('div.cke_toolbox');
            var $container = $('.ckeditor-container');
            var $content = $('#cke_id_content');
            var contentTop = $container.offset().top;
            var fixed = false;

            // Switch header and toolbar styles on scroll to keep them on screen
            $(doc).on('scroll', function() {

                // If top of the window is betwen top of #content and bottom of content + 200, the header is fixed
                var scrollTop = $(this).scrollTop();
                if (scrollTop >= contentTop) {

                    // Need to display or hide the toolbar depending on scroll position
                    if(scrollTop > $container.height() + contentTop - 200 /* offset to ensure toolbar doesn't reach content bottom */) {
                        $tools.css('display', 'none');
                        return; // Cut off at some point
                    }
                    else {
                        $tools.css('display', '');
                    }

                    // Fixed position toolbar if scrolled down to the editor
                    // Wrapped in IF to cut down on processing
                    if (!fixed) {
                        fixed = true;
                        $tools.css({
                            position: 'fixed',
                            top: 0,
                            width: $content.width() - 11
                        });
                    }

                } else { // If not, header is relative, put it back
                    if (fixed) {
                        fixed = false;
                        $tools.css({
                            position: 'relative',
                            top: 'auto',
                            width: 'auto'
                        });
                    }
                }
            });

            $(win).resize(function() { // Recalculate box width on resize
                if (fixed) {
                    $tools.css({
                        width: $container.width() - 10
                    }); // Readjust toolbox to fit
                }
            });
        };

        // Renders the WYSIWYG editor
        $textarea.each(function () {
            $(this).removeAttr('required').ckeditor(setup, {
                customConfig : '/en-US/docs/ckeditor_config.js'
            });
        });
    })();

    /*
        Calculate rendering max age in seconds from days, minutes and seconds
    */
    (function() {
        var seconds = $('#id_render_max_age').val();
        var getValue = function(selector) {
            return parseInt($(selector).val()) || 0;
        };

        var setAge = function() {
            $('#id_render_max_age').val(
                (((getValue('.duration-container #days') * 24) +
                getValue('.duration-container #hours')) * 60 +
                getValue('.duration-container #minutes')) * 60
            );
        };

        $('.duration-container input').on('change', setAge);

        if(seconds !== ''){
            //convert seconds to days, hours, minutes
            var days = Math.floor(seconds / (60 * 60 * 24));
            seconds -= days * (60 * 60 * 24);
            var hours = Math.floor(seconds / (60 * 60));
            seconds -= hours * (60 * 60);
            var minutes = Math.floor(seconds / 60);

            $('.duration-container #days').val(days);
            $('.duration-container #hours').val(hours);
            $('.duration-container #minutes').val(minutes);
        }else{
            setAge();
        }
    })();

    /*
        Switch to source
    */
    (function(){
        $('.doc-mode-btn').toggleMessage().on('click', function(e){
            e.preventDefault();

            var $source = $('.translate-source textarea');
            $('.translate-rendered, .translate-source').toggleClass('hidden');

            // Get height of textarea content, first time doc source is viewed
            if(!$source.data('height')){
                $source.height(function(){
                    return $(this).get(0).scrollHeight;
                });
                $source.data('height', true);
            }
        });

        $('.hide-original-btn').toggleMessage().on('click', function(e){
            e.preventDefault();

            $('#trans-content').toggleClass('translate-only');
        });
    })();

    /*
    Plugin for prepopulating the slug fields
  */
    $.fn.prepopulate = function(dependencies, maxLength) {
        var _changed = '_changed';

        return this.each(function() {
            var $field = $(this);

            $field.data(_changed, false);
            $field.on(_changed, function() {
                $field.data(_changed, true);
            });

            var populate = function () {
                // Bail if the fields value has changed
                if ($field.data(_changed) === true) {
                    return;
                }

                var values = [];
                var split;
                dependencies.each(function() {
                    if ($(this).val().length > 0) {
                        values.push($(this).val());
                    }
                });

                var s = values.join(' ');
                s = $.slugifyString(s, false, true);

                // Trim to first num_chars chars
                s = s.substring(0, maxLength);

                // Only replace the last piece (don't replace slug heirarchy)
                split = $field.val().split('/');
                split[split.length - 1] = s;
                $field.val(split.join('/'));
            };

            dependencies.on('keyup change focus', populate);
        });
    };

    /*
    Functionality to set up the new, edit, and translate pages
  */
    var $form = $('#wiki-page-edit');

    function init() {
        var $body = $('body');

        $('select.enable-if-js').removeAttr('disabled');

        // If the form is a translate form, update the $form object
        var $translateForm = $('#translate-document');
        if($translateForm.length) {
            $form = $translateForm;
        }

        if ($body.is('.new')) {
            initPrepopulatedSlugs();
        }

        if ($body.is('.edit, .new, .translate')) {
            initMetadataEditButton();
            initSaveAndEditButtons();
            initDirtinessTracking();
            initArticlePreview();
            initAttachmentsActions();
            initMetadataParentTranslation();
        }
    }

    function initPrepopulatedSlugs() {
        var fields = {
            title: {
                id: '#id_slug',
                dependencyIds: ['#id_title'],
                dependencyList: ['#id_title'],
                maxLength: 50
            }
        };

        $.each(fields, function(i, field) {
            $(field.id).addClass('prepopulated_field');
            $(field.id).data('dependencyList', field.dependencyList)
                .prepopulate($(field.dependencyIds.join(',')),
                    field.maxLength);
        });
    }

    /*
     * Initialize the article preview functionality.
     */
    function initArticlePreview() {
        $('.btn-preview').on('click', function(e) {
            e.preventDefault();

            // Ensure that content is available and exists
            var title = ' ';
            var $titleNode = $('#id_title');
            var data;

            if(CKEDITOR.instances.id_content) {
                data = $.trim(CKEDITOR.instances.id_content.getSnapshot());
            }
            else {
                return;
            }
            if($titleNode.length) {
                title = $titleNode.val();
            }

            // Since we have content, we can launch!
            if(data) {
                // Create and inject form for preview submission
                var $form = $('<form action="' + $(this).attr('data-preview-url') + '" target="previewWin" method="POST" />').appendTo(document.body);
                $('<input type="hidden" name="content" />').val(data).appendTo($form);
                $('<input type="hidden" name="title" />').val(title).appendTo($form);

                // Add the CSRF ?
                $('#wiki-page-edit, #translate-document').find('input[name=csrfmiddlewaretoken]').clone().appendTo($form);
                // Submit the form, and then get rid of it
                $form.get(0).submit();
                $form.remove();
            }

            return false;
        });
    }

    //
    // Initialize logic for metadata edit button.
    //
    function initMetadataEditButton () {

        if ($('#article-head .metadata').length) {
            var showMeta = function () {
                $('#article-head .metadata').show();
                $('#article-head .metadata #id_title').focus();
            };

            // Properties button reveals the metadata fields
            $('#btn-properties').on('click', function (ev) {
                ev.preventDefault();
                showMeta();
            });
            // Form errors reveal the metadata fields, since they're the most
            // likely culprits
            $('#edit-document .errorlist').each(showMeta);

        } else {
            $('#btn-properties').hide();
        }
    }

    //
    // Initialize logic for metadata parent translation
    //
    function initMetadataParentTranslation() {
        var $parentLis = $('.metadata-choose-parent');
        var $parentInput = $('#parent_id');

        $parentLis.each(function() {
            $(this).css('display', 'block');
            $('#parent_text').mozillaAutocomplete({
                minLength: 1,
                requireValidOption: true,
                autocompleteUrl: mdn.wiki.autosuggestTitleUrl,
                _renderItemAsLink: true,
                buildRequestData: function(req) {
                    req.locale = 'en-US';
                    return req;
                },
                onSelect: function(item) {
                    $parentInput.val(item.id);
                },
                onDeselect: function() {
                    $parentInput.val('');
                }
            });
        });
    }


    //
    // Initialize logic for save and save-and-edit buttons.
    //
    function initSaveAndEditButtons () {
        var $form = $('#wiki-page-edit');
        // Handle edits on the translate page
        if ($form.length === 0 && $('#translate-document').length === 1) {
            $form = $('#translate-document');
        }

        // save and edit attempts ajax submit
        $('.btn-save-and-edit').on('click', function() {
            // disable form
            $('#wiki-page-edit').attr('disabled', true);

            // Clear previous notification messages, if any
            $('.notification button.close').click();

            // give user feedback
            var saveNotification = mdn.Notifier.growl(gettext('Publishing changes…'), { duration: 0 , closable: true});

            // record event
            mdn.analytics.trackEvent({
                category: 'Wiki',
                action: 'Button', // now "Publish and keep editing" but keeping label for analytics continuity
                label: 'Save and Keep Editing'
            });

            // get form data
            var formData = $form.serialize();
            var formURL = window.location.href; // submits to self

            $.ajax({
                url : formURL + '?async',
                type: 'POST',
                data : formData,
                dataType : 'html',
                success: function(data, textStatus, jqXHR) {
                    // server came back 200
                    // was there an error, or did the session expire?
                    var $parsedData = $($.parseHTML(data));
                    var $responseErrors = $parsedData.find('.errorlist');
                    var $responseLoginRequired = $parsedData.find('#login');
                    var jsonErrorMessage;
                    try {
                        jsonErrorMessage = JSON.parse(jqXHR.responseText).error_message;
                    } catch (err) {
                        jsonErrorMessage = undefined;
                    }
                    // If there are errors, saveNotification() for them
                    if ($responseErrors.length) {
                        var $liErrors = $responseErrors.find('li');
                        saveNotification.error($liErrors);
                    // If there was an error from the json response, saveNotification() for it
                    } else if (typeof(jsonErrorMessage) !== 'undefined') {
                        saveNotification.error(gettext(jsonErrorMessage));
                    // Check if the session has timed out
                    } else if ($responseLoginRequired.length) {
                        saveNotification.error(gettext('Publishing failed. You are not currently signed in. Please use a new tab to sign in and try publishing again.'));
                    } else {
                        // assume it went well
                        saveNotification.success(gettext('Changes saved.'), 2000);

                        // We also need to update the form's current_rev to
                        // avoid triggering a conflict, since we just saved in
                        // the background.
                        var responseData = JSON.parse(data);
                        if (responseData.error === true) {
                            saveNotification.error(responseData.error_message);
                        } else {
                            var responseRevision = JSON.parse(data).new_revision_id;
                            $('input[id=id_current_rev]').val(responseRevision);

                            // Clear the review comment
                            $('#id_comment').val('');

                            // Trigger a `mdn:save-success` event so dirtiness can be reset throughout the page
                            $form.trigger('mdn:save-success');
                        }

                    }
                    // Re-enable the form; it gets disabled to prevent double-POSTs
                    $form.attr('disabled', false);
                },
                error: function(jqXHR) {
                    var errorMessage;
                    // Try to display the error that comes back from the server
                    try {
                        errorMessage = JSON.parse(jqXHR.responseText).error_message;
                    } catch (err) {
                        errorMessage = gettext('Publishing failed. Please copy and paste your changes into a safe place and try submitting the form using the "Publish" button.');
                    }
                    saveNotification.error(errorMessage);
                    // Re-enable the form; it gets disabled to prevent double-POSTs
                    $form.attr('disabled', false);
                }
            });
            /*
                //$form.find('input[name=current_rev]').val(

                //ir.attr('data-current-revision'));

                // Stop loading state on button
                //$('.btn-save-and-edit').removeClass('loading');

*/

        });
        $('.btn-save-and-edit').show();


        // Track submissions of the edit page form
        $form.on('submit', function() {
            mdn.analytics.trackEvent({
                category: 'Wiki',
                action: 'Form submission',
                label: 'Edit page'
            });
        });
    }


    function initAttachmentsActions() {
        var $attachmentsButton = $('#page-attachments-button');
        var $attachmentsNewTable = $('#page-attachments-new-table');
        var $attachmentsForm = $('#page-attachments-form');
        var $attachmentsFormCloneRow = $attachmentsNewTable.find('tbody tr').first();
        var $attachmentsNewTableActions = $attachmentsNewTable.find('tbody tr').last();
        var running = false;

        // If attachments are disabled, just hide the form
        if(!mdn.wiki.attachments_enabled) {
            $attachmentsButton.addClass('hidden');
            return;
        }

        // Upon click of the 'Attach Files' button, toggle display of upload table
        $attachmentsButton.on('click', function(e) {
            e.preventDefault();
            $attachmentsNewTable.toggleClass('hidden');
            if(!$attachmentsNewTable.hasClass('hidden')) {
                $attachmentsNewTable.find('input[type=text]').first()[0].focus();
            }
        });

        // Clicking the 'AMF' button adds more rows
        $('#page-attachments-more').on('click', function() {
            // Don't add boxes during submission
            if (running) {
                return;
            }
            function clone() {
                // Create and insert clone
                var $clone = $attachmentsFormCloneRow.clone();
                $clone.find('input, textarea').val('');
                $clone.find('.attachment-error').remove();
                $clone.insertBefore($attachmentsNewTableActions);
                $clone.addClass('dynamic-row');
                return $clone;
            }
            clone().find('input[type="text"]')[0].focus();
        });

        // Form submission, upload, and response handling
        $attachmentsForm.on('submit', function(e) {
            // Stop concurrent submissions
            if (running) {
                e.preventDefault();
                return;
            } else {
                running = true;
            }
        });
    }

    //
    // Initializes logic that keeps track of whether changes have been made to the article
    // So far three sections contribute to dirtiness: Metadata, editor content and tags
    //
    function initDirtinessTracking() {
        // These are all fields that count towards an edit, excluding the editor and tags
        var metaSelector = 'input:not([type="hidden"]), textarea, select';
        var $metaDataFields = $form.find(metaSelector);
        var editor = CKEDITOR.instances.id_content;

        function setEditorButtonsEnabled(enabled) {
            var saveContinue = editor.getCommand('mdn-buttons-save');
            var saveEdit = editor.getCommand('mdn-buttons-save-exit');

            var state = CKEDITOR.TRISTATE_OFF;
            if (!enabled) {
                state = CKEDITOR.TRISTATE_DISABLED;
            }
            if (saveContinue) {
                saveContinue.setState(state);
            }
            if (saveEdit) {
                saveEdit.setState(state);
            }
        }

        function onDirty() {
            $('.btn-save-and-edit').attr('disabled', false);
            $('.btn-save').attr('disabled', false);
            setEditorButtonsEnabled(true);
        }
        // Called when everything is clean
        function onClean() {
            $('.btn-save-and-edit').attr('disabled', true);
            $('.btn-save').attr('disabled', true);
            setEditorButtonsEnabled(false);
        }

        function resetDirty() {
            editor.resetDirty();
            $metaDataFields.each(function() {
                var $this = $(this);
                var value = $this.val();

                if($this.attr('type') === 'checkbox') {
                    value = this.checked;
                }

                $this.data('original', value);
            });
            $form.find('.dirty').removeClass('dirty');
            $form.trigger('mdn:clean');
        }

        // Three custom events are used to track changes throughout the page
        // Dirtiness is marked by the class `dirty`, cleanliness by `clean`
        $form.on('mdn:save-success', resetDirty)
            .on('mdn:dirty', onDirty)
            .on('mdn:clean', function() { // Gets triggered when a section is clean, others may still be dirty
                if (!$('.dirty').length) {
                    onClean();
                }
            });

        // Keep track of editor dirtiness
        function checkEditorDirtiness() {
            var editorDirty = editor.checkDirty();
            var $container = $form.find('.editor-container');

            if ($container.length) {
                if (editorDirty) {
                    $container.addClass('dirty').trigger('mdn:dirty');
                } else {
                    $container.removeClass('dirty').trigger('mdn:clean');
                }
            } else {
                /*
                 * When the editor is maximized, the container doesn't
                 * exist in the form, but we still need to fire mdn:dirty
                 * and mdn:clean events to enable and disable the save
                 * buttons in the editor. Fortunately, those events are
                 * handled on the form, so we just trigger the events
                 * directly on the form in that case, and we don't
                 * bother with adding and removing the 'dirty' class.
                 */
                if (editorDirty) {
                    $form.trigger('mdn:dirty');
                } else {
                    $form.trigger('mdn:clean');
                }
            }
        }

        var interval;
        editor.on('contentDom', function() {
            // Basic events we know trigger a change
            editor.document.on('keyup', checkEditorDirtiness);
            editor.on('paste setData', checkEditorDirtiness);

            // Since CKE doesn't provide us a change event yet, a constant check is still the best way to
            // determine if the editor has changed.
            if(interval) {
                clearInterval(interval);
            }
            interval = setInterval(checkEditorDirtiness, 1500); // 1 seconds is arbitrary, we can update as desired
        });
        editor.on('instanceReady', function(e) {
            if (e.editor === editor) {
                setEditorButtonsEnabled(false);
            }
        });

        $(win).on('beforeunload', function() {
            if(interval) {
                clearInterval(interval);
            }
        });


        // Keep track of metadata dirtiness
        $form.on('change input', metaSelector, function() {
            var $this = $(this);
            var value = $this.val();
            var typeAttr = $this.attr('type');

            if(typeAttr && typeAttr.toLowerCase() === 'checkbox') {
                value = this.checked;
            }

            if (value !== $this.data('original')) {
                if (!$this.hasClass('dirty')) {
                    $this.addClass('dirty').trigger('mdn:dirty');
                }
            } else {
                $this.removeClass('dirty').trigger('mdn:clean');
            }
        });

        resetDirty();
    }

    $(doc).ready(init);

}(jQuery, window, document));
