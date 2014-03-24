(function($, win) {

    /**
     * Set up for inline section editing.
     */
    function initSectionEditing () {
        // Wire up the wiki article with an event delegation handler
        $('body.document #wikiArticle').on('click', function (ev) {
            var target = $(ev.target);
            if (target.is('a.edit-section')) {
                // Caught a section edit link click.
                return handleSectionEditClick(ev, target);
            }
            if (target.is('.edited-section-ui.current .btn-save')) {
                // Caught a section edit save click.
                saveSectionEdit();
                return false;
            }
            if (target.is('.edited-section-ui.current .btn-cancel')) {
                // Caught a section edit cancel click.
                cancelSectionEdit();
                return false;
            }
        });
    }

    /**
     * Handle a click on a section editing link.
     */
    function handleSectionEditClick (ev, link) {
        // Any modifiers while clicking an edit link reverts to default
        // behavior (eg. open in new window)
        if (ev.metaKey || ev.altKey || ev.ctrlKey || ev.shiftKey) {
            return;
        }

        // Look up some details about the section refered to by the link
        var section_id = link.attr('data-section-id');
        var section_edit_url = link.attr('href');
        var section_src_url = link.attr('data-section-src-url');
        var section_el = $('#'+section_id);
        var section_tag = section_el[0].tagName.toUpperCase();

        // Bail if the referenced section element doesn't exist.
        if (!section_el.length) { return; }

        // Bail if the referenced section element is not a header.
        if (-1 == HEADERS.indexOf(section_tag)) { return; }

        // If there's a current editor, cancel it.
        if ($('.edited-section-ui.current').length) {
            if (!cancelSectionEdit()) {
                // The user cancelled the cancellation, so just ignore the
                // section edit click.
                return false;
            }
        }

        // Bail if the referenced section already appears to an edit in
        // progress. But, cancel the link click
        if (section_el.parents('div.edited-section').length) {
            return false;
        }

        // Build a stop selector from headers equal to or higher in rank
        var stop_pos = HEADERS.indexOf(section_tag)+1,
            stop_selector = HEADERS.slice(0, stop_pos).join(',');

        // Scoop up all the elements considered part of the section, wrap them
        // in a container while editing. Style it as loading, initially.
        var section_kids = section_el.nextUntil(stop_selector).andSelf();
        section_kids.wrapAll('<div class="edited-section edited-section-loading" ' +
                                     'id="edited-section"/>');

        // Start loading the current section source, launch editor when loaded.
        $.get(section_src_url, function (html_data) {
            launchSectionEditor(section_id, section_edit_url, html_data);
        });

        return false;
    }

    /**
     * Launch the section editor with HTML data.
     */
    function launchSectionEditor (section_id, section_edit_url, html_data) {
        // Clone and setup the editing UI from template
        var ui = $('.edited-section-ui.template').clone()
            .removeClass('template').addClass('current')
            .find('.src').html(html_data).end();

        // Inject the source block, and remove the edit block loading style.
        $('#edited-section')
            .before(ui)
            .removeClass('edited-section-loading');

        // Fire up the CKEditor, stash it in the UI's data store
        CKEDITOR.inlineHeight = ui.find('.src').height();
        CKEDITOR.inlineCallback = function() {
            ui.find('.edited-section-buttons').addClass('loaded');
        };
        $('.edited-section-ui.current')
            .data('edit_url', section_edit_url)
            .data('editor',
                CKEDITOR.replace(ui.find('.src')[0], {
                    customConfig : '/docs/ckeditor_config.js'
                }))
            .find('.btn-save').data('save_cb', saveSectionEdit).end();
    }

    /**
     * Cancel any current section editing.
     */
    function cancelSectionEdit () {
        // Make sure the user wants this to happen.
        var msg = $('#content-main > article').attr('data-cancel-edit-message');
        var rv = confirm(msg);

        if (!rv) { return false; }

        // We're sure, so clean up without committing.
        cleanupSectionEdit();
        return true;
    }

    /**
     * Save the results of section editing.
     */
    function saveSectionEdit () {
        var ui = $('.edited-section-ui.current');
        var edit_url = ui.data('edit_url');
        var editor = ui.data('editor');
        var article = $('#content-main > article');
        var current_rev = article.attr('data-current-revision');
        var refresh_msg = article.attr('data-refresh-message');
        var src = $('.edited-section-ui.current .src').html();

        ui.addClass('edited-section-ui-saving');
        editor.updateElement();

        $.ajax({
            type: 'POST',
            url: edit_url + '&raw=1',
            data: {
                'form': 'rev',
                'content': src,
                'current_rev': current_rev
            },
            error: function (xhr, status, err) {

                if ('409' == xhr.status) {
                    // We detected a conflict, most likely from a mid-air edit
                    // collision. So, use the hidden conflict-bouncer form to
                    // transition to a full-page resolution UI.
                    $('form.conflict-bouncer')
                        .attr('action', edit_url)
                        .find('input[name=current_rev]')
                            .val(current_rev).end()
                        .find('input[name=content]')
                            .val(src).end()
                        .submit();
                    return;
                }

                // Anything else error-wise is probably recoverable.
                ui.removeClass('.edited-section-ui-saving');

            },
            success: function (data, status, xhr) {

                if ('205' == xhr.status) {
                    // There wasn't a conflict after the edit, but something
                    // else on the page changed. So, we should refresh rather
                    // than just updating the edited section. That will help
                    // prevent conflicts in future section edits and alert the
                    // user that someone else is touching the page.
                    alert(refresh_msg);
                    win.location.reload();
                    return;
                }

                // Looks like we were the only editor so far, so carry on and
                // update the content inline.
                $('#edited-section').html(data)
                cleanupSectionEdit();

                // Also, since this should have been the only change, we can
                // update the local current revision ID to what the server
                // reported in a header.
                article.attr('data-current-revision', xhr.getResponseHeader('x-kuma-revision'))
            }
        });
    }

    /**
     * Clean up the changes made to support inline section editing.
     */
    function cleanupSectionEdit () {
        $('.edited-section-ui.current').each(function () {
            var ui = $(this);
            ui.data('editor').destroy();
            ui.remove();
        });
        $('#edited-section').children().unwrap();
    }

})(jQuery, window);
