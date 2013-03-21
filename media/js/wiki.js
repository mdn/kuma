/*
 * wiki.js
 * Scripts for the wiki app.
 * 
 */


(function ($, gettext) {
    var OSES, BROWSERS, VERSIONS, MISSING_MSG;
    var DRAFT_NAME, DRAFT_TIMEOUT_ID;

    var supportsLocalStorage = ('localStorage' in window),
        formId = 'wiki-page-edit',
        formSelector,
        isTranslation,
        isTemplate;

    function init() {
        $('select.enable-if-js').removeAttr('disabled');

        // If the form is a translate form, update the formId
        var translateFormId = 'wiki-page-translate';
        if($('#' + translateFormId).length) {
            formId = translateFormId;
            isTranslation = true;
        }
        formSelector = '#' + formId;

        var $body = $('body');

        if($body.hasClass('is-template')) {
            isTemplate = 1;
        }

        if ($body.is('.new')) {
            initPrepopulatedSlugs();
        }
        initDetailsTags();

        if ($body.is('.document') || $body.is('.home')) {  // Document page
            initHelpfulVote();
            initSectionEditing();
        } else if ($body.is('.review')) { // Review pages
            initApproveReject();
        }
        if ($body.is('.document')){
            initSyntaxHighlighter();
            initTabBox();
        }

        if ($body.is('.revert-document')) {
            initSyntaxHighlighter();
        }

        if ($body.is('.home')) {
            initClearOddSections();
        }

        if ($body.is('.edit, .new, .translate')) {
            initMetadataEditButton();
            initSaveAndEditButtons();
            initArticlePreview();
            initAttachmentsActions();
            if(!isTemplate) {
                initDrafting();
            }
            initMetadataParentTranslation();
            // initTitleAndSlugCheck();
            // initDrafting();
        }
        if ($body.is('.edit.is-template') || $body.is('.new.is-template')) {

            var textarea = $('textarea#id_content').hide();

            var editor = window.ace_editor = ace.edit('ace_content');
            editor.setTheme('ace/theme/dreamweaver');
            editor.setBehavioursEnabled(false);
            
            var JavaScriptMode = require('ace/mode/javascript').Mode;

            var session = editor.getSession();
            session.setMode(new JavaScriptMode());
            session.setValue(textarea.val());
            session.on('change', function(){
              textarea.val(editor.getSession().getValue());
            });
            initDrafting();
        }
        if ($body.is('.move-page')) {
           initPageMove();
        }
    }
    
    var HEADERS = [ 'HGROUP', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6' ];

    /**
     * Set up for inline section editing.
     */
    function initSectionEditing () {
        // If we don't have a #wikiArticle, bail out.
        var wiki_article = $('body.document #wikiArticle');
        if (!wiki_article.length) { return; }
        
        // Wire up the wiki article with an event delegation handler
        wiki_article.click(function (ev) {
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
        var section_id = link.attr('data-section-id'),
            section_edit_url = link.attr('href'),
            section_src_url = link.attr('data-section-src-url'),
            section_el = $('#'+section_id),
            section_tag = section_el[0].tagName.toUpperCase();

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
        var msg = $('#content-main > article')
                    .attr('data-cancel-edit-message'),
            rv = confirm(msg);
        if (!rv) { return false; }
        // We're sure, so clean up without committing.
        cleanupSectionEdit();
        return true;
    }

    /**
     * Save the results of section editing.
     */
    function saveSectionEdit () {
        var ui = $('.edited-section-ui.current'),
            edit_url = ui.data('edit_url'), 
            editor = ui.data('editor'),
            article = $('#content-main > article'),
            current_rev = article.attr('data-current-revision'),
            refresh_msg = article.attr('data-refresh-message');
            
        ui.addClass('edited-section-ui-saving');
        editor.updateElement();
        var src = $('.edited-section-ui.current .src').html();

        $.ajax({
            type: 'POST', url: edit_url + '&raw=1',
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
                alert('Error saving section, please try again.');
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
                    window.location.reload();
                    return;
                }

                // Looks like we were the only editor so far, so carry on and
                // update the content inline.
                $('#edited-section').html(data)
                cleanupSectionEdit();

                // Also, since this should have been the only change, we can
                // update the local current revision ID to what the server
                // reported in a header.
                article.attr('data-current-revision', 
                             xhr.getResponseHeader('x-kuma-revision'))
            
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

    // Add `odd` CSS class to home page content sections for older browsers.
    function initClearOddSections() {
        clearOddSections();
        $('#os, #browser').change(clearOddSections);
    }

    function clearOddSections() {
        var odd = true;
        $('#home-content-explore section').removeClass('odd');
        $('#home-content-explore section:visible').each(function(){
            // I can't use :nth-child(odd) because of showfor
            if (odd) {
                $(this).addClass('odd');
            }
            odd = !odd;
        });
    }

    // Make <summary> and <details> tags work even if the browser doesn't support them.
    // From http://mathiasbynens.be/notes/html5-details-jquery
    function initDetailsTags() {
        var supportsDetails = ('open' in document.createElement('details'));

        // Execute the fallback only if there's no native `details` support
        if (!supportsDetails) {
            // Note <details> tag support. Modernizr doesn't do this properly as of 1.5; it thinks Firefox 4 can do it, even though the tag has no "open" attr.
            document.documentElement.className += ' no-details';

            // Loop through all `details` elements
            $('details').each(function() {
                // Store a reference to the current `details` element in a variable
                var $details = $(this),
                    // Store a reference to the `summary` element of the current `details` element (if any) in a variable
                    $detailsSummary = $('summary', $details),
                    // Do the same for the info within the `details` element
                    $detailsNotSummary = $details.children(':not(summary)'),
                    // This will be used later to look for direct child text nodes
                    $detailsNotSummaryContents = $details.contents(':not(summary)');

                // If there is no `summary` in the current `details` element...
                if (!$detailsSummary.length) {
                    // ...create one with default text
                    $detailsSummary = $(document.createElement('summary')).text('Details').prependTo($details);
                }

                // Look for direct child text nodes
                if ($detailsNotSummary.length !== $detailsNotSummaryContents.length) {
                    // Wrap child text nodes in a `span` element
                    $detailsNotSummaryContents.filter(function() {
                        // Only keep the node in the collection if it's a text node containing more than only whitespace
                        return (this.nodeType === 3) && (/[^\t\n\r ]/.test(this.data));
                    }).wrap('<span>');
                    // There are now no direct child text nodes anymore -- they're wrapped in `span` elements
                    $detailsNotSummary = $details.children(':not(summary)');
                }

                // Hide content unless there's an `open` attribute
                if (typeof $details.attr('open') !== 'undefined') {
                    $details.addClass('open');
                    $detailsNotSummary.show();
                } else {
                    $detailsNotSummary.hide();
                }

                // Set the `tabindex` attribute of the `summary` element to 0 to make it keyboard accessible
                $detailsSummary.attr('tabindex', 0).click(function() {
                    // Focus on the `summary` element
                    $detailsSummary.focus();
                    // Toggle the `open` attribute of the `details` element
                    if (typeof $details.attr('open') !== 'undefined') {
                        $details.removeAttr('open');
                    }
                    else {
                        $details.attr('open', 'open');
                    }
                    // Toggle the additional information in the `details` element
                    $detailsNotSummary.slideToggle();
                    $details.toggleClass('open');
                }).keyup(function(event) {
                    if (13 === event.keyCode || 32 === event.keyCode) {
                        // Enter or Space is pressed -- trigger the `click` event on the `summary` element
                        // Opera already seems to trigger the `click` event when Enter is pressed
                        if (!($.browser.opera && 13 === event.keyCode)) {
                            event.preventDefault();
                            $detailsSummary.click();
                        }
                    }
                });
            });
        }
    }

    // Return the browser and version that appears to be running. Possible
    // values resemble {fx4, fx35, m1, m11}. Return undefined if the currently
    // running browser can't be identified.
    function detectBrowser() {
        function getVersionGroup(browser, version) {
            if ((browser === undefined) || (version === undefined) || !VERSIONS[browser]) {
                return;
            }

            for (var i = 0; i < VERSIONS[browser].length; i++) {
                if (version < VERSIONS[browser][i][0]) {
                    return browser + VERSIONS[browser][i][1];
                }
            }
        }
        return getVersionGroup(BrowserDetect.browser, BrowserDetect.version);
    }

    // Treat the hash fragment of the URL as a querystring (e.g.
    // #os=this&browser=that), and return an object with a property for each
    // param. May not handle URL escaping yet.
    function hashFragment() {
        var o = {},
            args = document.location.hash.substr(1).split('&'),
            chunks;
        for (var i = 0; i < args.length; i++) {
            chunks = args[i].split('=');
            o[chunks[0]] = chunks[1];
        }
        return o;
    }

    // Hide/show the proper page sections that are marked with {for} tags as
    // applying to only certain browsers or OSes. Update the table of contents
    // to reflect what was hidden/shown.
    function initForTags() {
        var $osMenu = $('#os'),
            $browserMenu = $('#browser'),
            $origBrowserOptions = $browserMenu.find('option').clone(),
            $body = $('body'),
            hash = hashFragment(),
            isSetManually;

        OSES = $osMenu.data('oses');  // {'mac': true, 'win': true, ...}
        BROWSERS = $browserMenu.data('browsers');  // {'fx4': true, ...}
        VERSIONS = $browserMenu.data('version-groups');  // {'fx': [[3.4999, '3'], [3.9999, '35']], 'm': [[1.0999, '1'], [1.9999, '11']]}
        MISSING_MSG = gettext('[missing header]');

        // Make the 'Table of Contents' header localizable.
        $('#toc > h2').text(gettext('Table of Contents'));

        function updateForsAndToc() {
            // Hide and show document sections accordingly:
            showAndHideFors($('select#os').val(),
                            $('select#browser').val());

            // Update the table of contents in case headers were hidden or shown:
            $('#toc > :not(h2)').remove(); // __TOC__ generates <ul/>'s.
            $('#toc').append(filteredToc($('#doc-content'), '#toc h2'));

            return false;
        }

        // If there isn't already a hash for purposes of actual navigation,
        // stick our {for} settings in there.
        function updateHashFragment() {
            var hash = hashFragment();

            // Kind of a shortcut. What we really want to know is "Is there anything in the hash fragment that isn't a {for} selector?"
            if (!document.location.hash || hash.hasOwnProperty("os") || hash.hasOwnProperty("browser")) {
                var newHash = "os=" + $osMenu.val() + "&browser=" + $browserMenu.val();
                document.location.replace(document.location.href.split('#')[0] + '#' + newHash);
            }
        }

        // Persist the menu selection in a cookie and hash fragment.
        function persistSelection() {
            $.cookie("for_os", $osMenu.val(), {path: '/'});
            $.cookie("for_browser", $browserMenu.val(), {path: '/'});
            updateHashFragment();
        }

        // Clear the menu selection cookies.
        function clearSelectionCookies() {
            $.cookie("for_os", null, {path: '/'});
            $.cookie("for_browser", null, {path: '/'});
        }

        // Get the dependency based on the currently selected OS
        function getCurrentDependency() {
            return $osMenu.find('[value="' + $osMenu.val() + '"]')
                          .data('dependency');
        }

        //Handle OS->Browser dependencies
        function handleDependencies(evt, noRedirect) {
            var currentDependency = getCurrentDependency(),
                currentBrowser, newBrowser, availableBrowsers;

            if (!noRedirect && $body.is('.home') &&
                !$body.is('.' + currentDependency)) {
                // If we are on the mobile page and select a desktop OS,
                // redirect to the desktop home page. And vice-versa.
                // TODO: maybe use data-* attrs for the URLs?
                persistSelection();
                var url = document.location.href;
                if ($body.is('.mobile')) {
                    document.location = url.replace('/mobile', '/home');
                } else {
                    document.location = url.replace('/home', '/mobile');
                }
            }

            currentBrowser = $browserMenu.val();
            availableBrowsers = $origBrowserOptions.filter(
                '[data-dependency="' + currentDependency + '"]');
            $browserMenu.empty().append(availableBrowsers);

            // Set browser to same version (frex, m4->fx4), if possible.
            var version = currentBrowser.replace(/^\D+/,'');
            $browserMenu.find('option').each(function() {
                var $this = $(this);
                if ($this.val().replace(/^\D+/,'') == version) {
                    $browserMenu.val($this.val());
                }
            });
            //updateShowforSelectors();
        }

        // Select the right item from the browser or OS menu, taking cues from
        // the following places, in order: the URL hash fragment, the cookie,
        // and client detection. Return whether the item appears to have
        // selected manually: that is, via a cookie or a hash fragment.
        function setSelectorValue(cookieName, hashName, hash, detector, $menu) {
            var initial = hash[hashName]
                isManual = true;
            if (!initial) {
                initial = $.cookie(cookieName);
                if (!initial) {
                    initial = detector();
                    isManual = false;
                }
            }
            if (initial) {
                $menu.val(initial);  // does not fire change event
                //updateShowforSelectors();
            }
            return isManual;
        }

        // Set the selector value to the first option that doesn't
        // have the passed in dependency.
        function setSelectorDefault($select, dependency) {
            $select.val(
                $select.find('option:not([data-dependency="' + dependency +
                             '"]):first').attr('value'));
        }

        // If we are on home page, make sure appropriate OS is selected
        function checkSelectorValues() {
            var currentDependency,
                isManual = false;

            if ($body.is('.home')) {
                currentDependency = getCurrentDependency();
                // currentDependency will be 'desktop' or 'mobile'
                // Make sure we are on the corresponding home page. Otherwise,
                // change the selection appropriately.
                if (!$body.is('.' + currentDependency)) {
                    var $detectedOS = $osMenu.find('[value=' + BrowserDetect.OS + ']');
                    if ($detectedOS.data('dependency') != currentDependency) {
                        // The detected OS is valid. Make it the new selection.
                        $osMenu.val($detectedOS.attr('value'));
                        $browserMenu.val(detectBrowser());
                        clearSelectionCookies();
                    } else {
                        // Force a new selection.
                        setSelectorDefault($osMenu, currentDependency);
                        setSelectorDefault($browserMenu, currentDependency);

                        // Set the cookie so that the selection sticks when
                        // browsing to articles.
                        persistSelection();
                        isManual = true;
                    }
                }
            }
            return isManual;
        }

        // Select the sniffed, cookied, or hashed browser or OS if there is one:
        isSetManually = setSelectorValue("for_os", "os", hash, function() { return BrowserDetect.OS; }, $osMenu);
        isSetManually |= setSelectorValue("for_browser", "browser", hash, detectBrowser, $browserMenu);
        isSetManually |= checkSelectorValues();

        // Possibly change the settings based on dependency rules:
        handleDependencies(null, true);

        if (isSetManually) {
            updateHashFragment();
        }

        $osMenu.change(handleDependencies);
        $osMenu.change(persistSelection);
        $osMenu.change(updateForsAndToc);
        $browserMenu.change(persistSelection);
        $browserMenu.change(updateForsAndToc);

        // Fire off the change handler for the first time:
        updateForsAndToc();
    }

    function initPrepopulatedSlugs() {
        var fields = {
            title: {
                id: '#id_slug',
                dependency_ids: ['#id_title'],
                dependency_list: ['#id_title'],
                maxLength: 50
            }
        };

        $.each(fields, function(i, field) {
            $(field.id).addClass('prepopulated_field');
            $(field.id).data('dependency_list', field.dependency_list)
                   .prepopulate($(field.dependency_ids.join(',')),
                                field.maxLength);
        });
    }

    function initSyntaxHighlighter() {
        $('pre').each(function() {
            var $this = $(this),
                newText = $this.text().replace(/<span class="nowiki">(.*)<\/span>/g, '$1');
            $this.text(newText);
        });
        SyntaxHighlighter.defaults.toolbar = false;
        SyntaxHighlighter.defaults['auto-links'] = false;
        SyntaxHighlighter.all();
    }

    // Return a table of contents (an <ol>) listing the visible headers within
    // elements in the $pageBody set.
    //
    // The highest header level found within $pageBody is considered to be the
    // top of the TOC: if $pageBody has h2s but no h1s, h2s will be used as the
    // first level of the TOC. Missing headers (such as if you follow an h2
    // directly with an h4) are noted prominently so you can fix them.
    //
    // excludesSelector is an optional jQuery selector for excluding certain
    // headings from the table of contents.
    function filteredToc($pageBody, excludesSelector) {
        function headerLevel(index, hTag) {
            return parseInt(hTag.tagName.charAt(1), 10);
        }

        var $headers = $pageBody.find(':header:not(:hidden)'),  // :hidden is a little overkill, but it's short.
            $root = $('<ol />'),
            $cur_ol = $root,
            ol_level = Math.min.apply(Math, $headers.map(headerLevel).get());

        // For each header in the document, look upward until you hit something that's hidden. If nothing is found, add the header to the TOC.
        $headers.each(function addIfShown(index) {
            var h_level = headerLevel(0, this),
                $h = $(this);

            if (h_level > 4) {
                // Don't go any deeper than h4
                return;
            }

            if (excludesSelector && $h.is(excludesSelector)) {
                // Skip excluded headers.
                return;
            }

            // If we're too far down the tree, walk up it.
            for (; ol_level > h_level; ol_level--) {
                $cur_ol = $cur_ol.parent().closest('ol');
            }

            // If we're too far up the tree, walk down it, create <ol>s until we aren't:
            for (; ol_level < h_level; ol_level++) {
                var $last_li = $cur_ol.children().last();
                if ($last_li.length === 0) {
                    $last_li = $('<li />').append($('<em />')
                                                  .text(MISSING_MSG))
                                          .appendTo($cur_ol);
                }
                // Now the current <ol> ends in an <li>, one way or another.
                $cur_ol = $('<ol />').appendTo($last_li);
            }

            // Now $cur_ol is at exactly the right level to add a header by appending an <li>.
            // Clone the header, remove any hidden elements and get the text,
            // and replace back with the clone.
            var $tmpClone = $h.clone(),
                text = $h.find(':hidden').remove().end().text();
            $h.replaceWith($tmpClone);
            $cur_ol.append($('<li />').text(text).wrapInner($('<a>').attr('href', '#' + $h.attr('id'))));
        });
        return $root;
    }

    // Set the {for} nodes to the proper visibility for the given OS and
    // browser combination.
    //
    // Hidden are {for}s that {list at least one OS but not the passed-in one}
    // or that {list at least one browser but not the passed-in one}. Also, the
    // entire condition can be inverted by prefixing it with "not ", as in {for
    // not mac,linux}.
    function showAndHideFors(os, browser) {
        $('.for').each(function(index) {
            var osAttrs = {}, browserAttrs = {},
                foundAnyOses = false, foundAnyBrowsers = false,
                forData,
                isInverted,
                shouldHide;

            // Catch the "not" operator if it's there:
            forData = $(this).data('for');
            if (!forData) {
                // If the data-for attribute is missing, move on.
                return;
            }

            isInverted = forData.substring(0, 4) == 'not ';
            if (isInverted) {
                forData = forData.substring(4);  // strip off "not "
            }

            // Divide {for} attrs into OSes and browsers:
            $(forData.split(',')).each(function(index) {
                if (OSES[this] != undefined) {
                    osAttrs[this] = true;
                    foundAnyOses = true;
                } else if (BROWSERS[this] != undefined) {
                    browserAttrs[this] = true;
                    foundAnyBrowsers = true;
                }
            });

            shouldHide = (foundAnyOses && osAttrs[os] == undefined) ||
                         (foundAnyBrowsers && browserAttrs[browser] == undefined);
            if ((shouldHide && !isInverted) || (!shouldHide && isInverted)) {
                $(this).hide();  // saves original visibility, which is nice but not necessary
            }
            else {
                $(this).show();  // restores original visibility
            }
        });
    }

    /*
     * Initialize the article preview functionality.
     */
    function initArticlePreview() {
        $('#btn-preview').click(function(e) {
            e.preventDefault();
            
            // Ensure that content is available and exists
            var title = ' ', 
                $titleNode = $('#id_title'),
                data;
                
            if(CKEDITOR.instances['id_content']) {
                data = $.trim(CKEDITOR.instances['id_content'].getSnapshot());
            }
            else if(ace_editor && ace_editor) {
                data = $.trim(ace_editor.getSession().getValue());
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
                var $form = $("<form action='" + $(this).attr("data-preview-url") + "' target='previewWin' method='POST' />").appendTo(document.body);
                $("<input type='hidden' name='content' />").val(data).appendTo($form);
                $("<input type='hidden' name='title' />").val(title).appendTo($form);
                
                // Add the CSRF ?
                $('#csrfmiddlewaretoken').clone().appendTo($form);
                
                // Submit the form, and then get rid of it
                $form.get(0).submit();
                $form.remove();
            }
            
            return false;
        });
    }

    /*
     * Ajaxify the Helpful/NotHelpful voting form on Document page
     */
    var voted = false;
    function initHelpfulVote() {
        var $btns = $('#helpful-vote input[type="submit"]');
        $btns.click(function(e) {
            if (!voted) {
                var $btn = $(this),
                    $form = $btn.closest('form'),
                    data = {};
                $btns.attr('disabled', 'disabled');
                $form.addClass('busy');
                data[$btn.attr('name')] = $btn.val();
                $.ajax({
                    url: $btn.closest('form').attr('action'),
                    type: 'POST',
                    data: data,
                    dataType: 'json',
                    success: function(data) {
                        showMessage(data.message, $btn);
                        $btn.addClass('active');
                        $btns.removeAttr('disabled');
                        $form.removeClass('busy');
                        voted = true;
                    },
                    error: function() {
                        var msg = gettext('There was an error generating the preview.');
                        showMessage(msg, $btn);
                        $btns.removeAttr('disabled');
                        $form.removeClass('busy');
                    }
               });
            }

            $(this).blur();
            e.preventDefault();
            return false;
        });
    }

    function showMessage(message, $showAbove) {
        var $html = $('<div class="message-box"><p></p></div>'),
            offset = $showAbove.offset();
        $html.find('p').html(message);
        $('body').append($html);
        $html.css({
            top: offset.top - $html.height() - 30,
            left: offset.left + $showAbove.width()/2 - $html.width()/2
        });
        var timer = setTimeout(fadeOut, 10000);
        $('body').one('click', fadeOut);

        function fadeOut() {
            $html.fadeOut(function(){
                $html.remove();
            });
            $('body').unbind('click', fadeOut);
            clearTimeout(timer);
        }
    }

    function updateShowforSelectors() {
        $('#support-for input.selectbox, #support-for div.selectbox-wrapper').remove();
        $('#support-for select').selectbox();
    }

    function initTitleAndSlugCheck() {
        $('#id_title').change(function() {
            var $this = $(this),
                $form = $this.closest('form'),
                title = $this.val(),
                slug = $('#id_slug').val();
            verifyTitleUnique(title, $form);
            // Check slug too, since it auto-updates and doesn't seem to fire
            // off change event.
            verifySlugUnique(slug, $form);
        });
        $('#id_slug').change(function() {
            var $this = $(this),
                $form = $this.closest('form'),
                slug = $('#id_slug').val();
            verifySlugUnique(slug, $form);
        });

        function verifyTitleUnique(title, $form) {
            var errorMsg = gettext('A document with this title already exists in this locale.');
            verifyUnique('title', title, $('#id_title'), $form, errorMsg);
        }

        function verifySlugUnique(slug, $form) {
            var errorMsg = gettext('A document with this slug already exists in this locale.');
            verifyUnique('slug', slug, $('#id_slug'), $form, errorMsg);
        }

        function verifyUnique(fieldname, value, $field, $form, errorMsg) {
            $field.removeClass('error');
            $field.parent().find('ul.errorlist').remove();
            var data = {};
            data[fieldname] = value;
            $.ajax({
                url: $form.data('json-url'),
                type: 'GET',
                data: data,
                dataType: 'json',
                success: function(json) {
                    // Success means we found an existing doc
                    var docId = $form.data('document-id');
                    if (!docId || (json.id && json.id !== parseInt(docId))) {
                        // Collision !!
                        $field.addClass('error');
                        $field.before(
                            $('<ul class="errorlist"><li/></ul>')
                                .find('li').text(errorMsg).end()
                        );
                    }
                },
                error: function(xhr, error) {
                    if(xhr.status === 404) {
                        // We are good!!
                    } else {
                        // Something went wrong, just fallback to server-side
                        // validation.
                    }
                }
            });
        }
    }

    //
    // Initialize logic for metadata edit button.
    //
    function initMetadataEditButton () {
        if ($('#article-head .metadata').length > 0) {

            var show_meta = function (ev) {
                // Disable and hide the save-and-edit button when editing
                // metadata, since that can change the URL of the page and
                // tangle up where the iframe posts.
                ev.preventDefault();
                $('#article-head .title').hide();
                $('#article-head .metadata').show();
                $('#article-head .metadata #id_title').focus();
            }

            // Properties button reveals the metadata fields
            $('#btn-properties').click(show_meta);
            // Form errors reveal the metadata fields, since they're the most
            // likely culprits
            $('#edit-document .errorlist').each(show_meta);

        } else {
            $('#btn-properties').hide();
        }
    }
    
    // 
    // Initialize logic for metadata parent translation
    // 
    function initMetadataParentTranslation() {
        var $parentLi = $('#article-head .metadata .metadata-choose-parent'),
            $parentInput = $('#parent_id');
        if($parentLi.length) {
            $parentLi.css('display', 'block');
            $('#parent_text').mozillaAutocomplete({
                minLength: 1,
                requireValidOption: true,
                autocompleteUrl: $('#autosuggestTitleUrl').attr('data-url'),
                _renderItemAsLink: true,
                buildRequestData: function(req) {
                    req.locale = 'en-US';
                    return req;
                },
                onSelect: function(item, isSilent) {
                    $parentInput.val(item.id);
                },
                onDeselect: function(item) {
                    $parentInput.val('');
                }
            });
        }
    }
    

    //
    // Generates a storage key to be used by new, edit, translate, and translate-edit purposes
    // Ensures same key used by all functionalities in this file
    // Uses slashes as delimiters because they can't be used in slugs to edge name clashes based on
    // slug can be prevented
    // 
    function getStorageKey() {
        var noEdit = location.pathname.replace('$edit', ''),
            finalKey;
        if(isTranslation) { // Translation interface
            finalKey = 'draft/translate' + noEdit + '/' + location.search.replace('?tolocale=', '');
            finalKey = finalKey.replace('$translate', '');
        }
        else if($('#id_current_rev').val()) { // Edit
            finalKey = 'draft/edit' + noEdit;
        }
        else { // New
            finalKey = 'draft/new';
        }

        // Add another identifier for templates
        if(isTemplate) {
            finalKey += '/template';
        }

        return $.trim(finalKey);
    }

    // Injects a DIV with language to the effect of "you had a previous draft, want to restore it?"
    // This takes the place of an ugly, ugly confirmation box :(
    var $draftDiv;
    function displayDraftBox(content) {
        var text = gettext('You have a draft in progress.  <a href="" class="restoreLink">Restore the draft content</a> or <a href="" class="discardLink">discard the draft</a>.'),
            $contentNode = $('#id_content'),
            editor;

        // Plan the draft into the page
        $draftDiv = $('<div class="notice"><p>' + text + '</p></div>').insertBefore($contentNode);

        // Hook up the "restore" link
        $draftDiv.find('.restoreLink').click(function(e) {
            e.preventDefault();
            $contentNode.val(content);

            if(isTemplate) {
                editor = ace_editor;
                ace_editor.session.setValue(content);
            }
            else {
                editor = $contentNode.ckeditorGet();
                editor.setData(content);
            }
            editor.focus();
            
            updateDraftState('loaded');
            hideDraftBox();
        });

        // Hook up the "dispose" link 
        $draftDiv.find('.discardLink').click(function(e) {
            e.preventDefault();
            hideDraftBox();
            clearDraft(getStorageKey());
        });
    }
    function hideDraftBox() {
        $draftDiv && $draftDiv.css('display', 'none');
    }


    //
    // Initialize logic for save and save-and-edit buttons.
    // 
    function initSaveAndEditButtons () {
        var STORAGE_NAME = getStorageKey();

        // Save button submits to top-level
        $('#btn-save').click(function () {
            if (supportsLocalStorage) {
                // Clear any preserved content.
                localStorage.removeItem(STORAGE_NAME);
            }
            $(formSelector)
                .attr('action', '')
                .removeAttr('target');
            return true;
        });

        // Save-and-edit submits to a hidden iframe, style the button with a
        // loading anim.
        var savedTa;
        $('#btn-save-and-edit').click(function () {
            savedTa = $(formSelector + ' textarea[name=content]').val();
            if (supportsLocalStorage) {
                // Preserve editor content, because saving to the iframe can
                // yield things like 403 / login-required errors that bust out
                // of the frame
                localStorage.setItem(STORAGE_NAME, savedTa);
            }
            // Redirect the editor form to the iframe.
            $(formSelector)
                .attr('action', '?iframe=1')
                .attr('target', 'save-and-edit-target');
            // Change the button to a loading state style
            $(this).addClass('loading');
            return true;
        });
        $('#btn-save-and-edit').show();

        $('#save-and-edit-target').load(function () {
            if (supportsLocalStorage) {
                var if_doc = $('#save-and-edit-target')[0].contentDocument;
                if (typeof(if_doc) != 'undefined') {

                    var ir = $('#iframe-response', if_doc);
                    if ('OK' == ir.attr('data-status')) {

                        // Dig into the iframe on load and look for "OK". If found,
                        // then it should be safe to throw away the preserved content.
                        localStorage.removeItem(STORAGE_NAME);

                        // We also need to update the form's current_rev to
                        // avoid triggering a conflict, since we just saved in
                        // the background.
                        $(formSelector + ' input[name=current_rev]').val(
                            ir.attr('data-current-revision'));
                        
                    } else if ($(formSelector, if_doc).hasClass('conflict')) {
                        // HACK: If we detect a conflict in the iframe while
                        // doing save-and-edit, force a full-on save in order
                        // to surface the issue. There's no easy way to bust
                        // the iframe otherwise, since this was a POST.
                        $(formSelector)
                            .attr('action', '')
                            .attr('target', '');
                        $('#btn-save').click();
                    
                    }
                    
                    // Anything else that happens (eg. 403 errors) should have
                    // framebusting code to escape the hidden iframe.
                }
            }
            // Stop loading state on button
            $('#btn-save-and-edit').removeClass('loading');
            // Clear the review comment
            $('#id_comment').val('');
            // Re-enable the form; it gets disabled to prevent double-POSTs
            $(formSelector)
                .data('disabled', false)
                .removeClass('disabled');
            return true;
        });

    }

    function updateDraftState(action) {
        var now = new Date();
        nowString = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
        $('#draft-action').text(action);
        $('#draft-time').attr('title', now.toISOString()).text(nowString);
    }

    function saveDraft() {
        if (supportsLocalStorage) {
            localStorage.setItem(DRAFT_NAME, $(formSelector + ' textarea[name=content]').val());
            updateDraftState(gettext('saved'));
        }
    }

    function clearDraft(key) {
        if (supportsLocalStorage) {
           localStorage.removeItem(key);
        }
    }

    function initDrafting() {
        var editor;
        DRAFT_NAME = getStorageKey();

        if (supportsLocalStorage) {
            var prev_draft = localStorage.getItem(DRAFT_NAME);
            if (prev_draft){
                // draft matches server so discard draft
                if ($.trim(prev_draft) == $(formSelector + ' textarea[name=content]').val().trim()) {
                    clearDraft(DRAFT_NAME);
                } else {
                    displayDraftBox(prev_draft);
                }
            }
        }

        // Add key listener for CKEditor and drafting
        var callback = function() {
            clearTimeout(DRAFT_TIMEOUT_ID);
            DRAFT_TIMEOUT_ID = setTimeout(saveDraft, 3000);
        };
        if(isTemplate) {
            ace_editor.on && ace_editor.on('change', callback);
        }
        else {
            $('#id_content').ckeditorGet().on('key', callback);
        }

        // 
       $('#btn-discard').click(function() {
            clearTimeout(DRAFT_TIMEOUT_ID);
           clearDraft(DRAFT_NAME);
       });
    }

    function initApproveReject() {

        var approveModal = $('#approve-modal'),
            rejectModal = $('#reject-modal');

        $('#btn-approve').click(function() {
            approveModal.show();
            rejectModal.hide();
        });
        approveModal.hide();
        $('#btn-reject').click(function() {
            rejectModal.show();
            approveModal.hide();
        });
        rejectModal.hide();
    }


    function initTabBox() {
        $('.htab').each(function(index) {
            var $htab = $(this),
                $items = $htab.find('>ul>li');

            $htab.append($('div[id=compat-desktop]')[index]);
            $htab.append($('div[id=compat-mobile]')[index]);

            $items.find('a').click(function() {
                var $this = $(this)
                $items.removeClass('selected');
                $this.parent().addClass('selected');
                $htab.find('>div').hide().eq($items.index($this.parent())).show();
            }).eq(0).click();
        });
    }

    function initAttachmentsActions() {
        var $attachmentsTable = $('#page-attachments-table'),
            $attachmentsCount = $('#page-attachments-count'),
            $attachmentsButton = $('#page-attachments-button'),
            $attachmentsNoMessage = $('#page-attachments-no-message'),
            $attachmentsNewTable = $('#page-attachments-new-table'),
            $attachmentsForm = $('#page-attachments-form'),
            $attachmentsFormCloneRow = $attachmentsNewTable.find('tbody tr').first(),
            $attachmentsNewTableActions = $attachmentsNewTable.find('tbody tr').last(),
            $pageAttachmentsSpinner = $('#page-attachments-spinner'),
            $iframe = $('#page-attachments-upload-target'),
            uploadFormTarget = $attachmentsForm.length && $attachmentsForm.attr('action'),
            running = false;

        // If no attachments table, get out -- no permissions
        if(!$attachmentsTable.length) {
            return;
        }

        // Upon click of the 'Attach Files' button, toggle display of upload table
        $attachmentsButton.bind('click', function(e) {
            e.preventDefault();
            $attachmentsNewTable.toggleClass('hidden');
            if(!$attachmentsNewTable.hasClass('hidden')) {
                $attachmentsNewTable.find('input[type=text]').first()[0].focus();
            }
        });

        // Clicking the 'AMF' button adds more rows
        $('#page-attachments-more').bind('click', function() {
            // Don't add boxes during submission
            if(running) return;
            function clone() {
                // Create and insert clone
                $clone = $attachmentsFormCloneRow.clone();
                $clone.find('input, textarea').val('');
                $clone.find('.attachment-error').remove();
                $clone.insertBefore($attachmentsNewTableActions);
                $clone.addClass('dynamic-row');

                // Show the cell actions now!
                $attachmentsNewTable.find('.page-attachment-actions-cell').removeClass('hidden');
                $clone.find('.delete-attachment').removeClass('hidden');

                return $clone;
            }
            var firstClone = clone();
            firstClone.find('input[type="text"]')[0].focus();
        });

        // Add an "ajax" parameter to the form for the sake of the server
        $("<input type='hidden' name='is_ajax' value='1' />").appendTo($attachmentsForm);

        // Submitting the form posts to mystical iframe
        $iframe.bind('load', function(e) {
            running = false;
            $attachmentsForm.data('disabled', false);

            // Handle results
            try {
                var $textarea = $iframe.contents().find('textarea').first(),
                    validIndexes = [],
                    invalidIndexes = [],
                    dynamicRows,
                    result;
                if($textarea.length) {
                    // Get JSON
                    result = JSON.parse($.trim($textarea.val()));
                    // Add error messages where needed, or hide all new rows
                    $dynamicRows = $attachmentsNewTable.find('.dynamic-row');
                    // Add the row to the table
                    $.each(result, function(i) {
                        // If valid....
                        if(this.id) {
                            // Add to uploads table
                            var $newTr = $(this.html);
                            $newTr.appendTo($attachmentsTable);
                            $newTr.addClass('new-row');
                            // Update attachment count
                            $attachmentsCount.text(parseInt($attachmentsCount.text(), 10) + 1);
                            // Add item to list
                            if(window.MDN_ATTACHMENTS) {
                                window.MDN_ATTACHMENTS.push(this);
                            }
                            validIndexes.push(i);
                            // Remove the form row
                            if(!i) { // First row
                                $attachmentsFormCloneRow.find('input, textarea').val('');
                            }
                            else {
                                var node = $dynamicRows.eq(i)[0];
                                $dynamicRows[i] = '';
                                node.parentNode.removeChild(node);
                            }
                        }
                        else { // Error!
                            invalidIndexes.push(i);
                        }

                    });

                    // Hide the 'no rows' paragraph, show table
                    $attachmentsNoMessage.addClass('hidden');
                    $attachmentsTable.removeClass('hidden');

                    // If all good, we can reset the form
                    if(validIndexes.length == result.length) {
                        // Reset the entire form
                        $attachmentsForm[0].reset();
                        $dynamicRows.remove();
                    }
                    else { // We have to cherry pick which were good and which were bad
                        $.each(invalidIndexes, function() {
                            if(this == 0) {
                                // Add message to the clone row
                                $('<div class="attachment-error"></div>')
                                    .appendTo($attachmentsFormCloneRow.find('.page-attachment-actions-file-cell'))
                                    .text(result[this]['error'])
                            }
                        });
                    }
                }
                else {
                    // Show error message?
                    console.warn('No textarea')
                }
            }
            catch(e) {
                // Show error message? 
                console.warn('Exception! ', e);
            }
            $pageAttachmentsSpinner.css('opacity', 0);
        });

        // Form submission, upload, and response handling
        $attachmentsForm.attr('target', 'page-attachments-upload-target').bind('submit', function(e) {
            // Stop concurrent submissions
            if(running) return;
            // Hide all error messages
            $attachmentsNewTable.find('.attachment-error').remove();
            // IE....
            var valid = true;
            $attachmentsNewTable.find('input[required], textarea[required]').each(function() {
                var $this = $(this);
                if($this.val() == '') {
                    e.preventDefault();
                    e.stopPropagation();
                    $this.addClass('attachment-required');
                    valid = false;
                }
                else {
                    $this.removeClass('attachment-required');
                }
            });
            if(!valid) {
                running = false;
                setTimeout(function() { $attachmentsForm.data('disabled', false); }, 200);
                return;
            }

            // Show the spinner
            $pageAttachmentsSpinner.css("opacity", 1);
        });
    }
    
    function initPageMove() {
         // Retrieve request and move information
         var $moveSlug = $('#moveSlug'),
             $suggestionInput = $('#parentSuggestion'),
             $suggestionContainer= $('.parentSuggestContainer'),
             $lookupLink = $('.moveLookupLink'),
             specific_slug = $('#currentSlug').val(),
             moveLocale = $('#moveLocale').val(),
             onHide = function() {
                 $suggestionContainer.removeClass('show');
                 $moveSlug[0].focus();
                 $suggestionInput.mozillaAutocomplete('clear');
                 $suggestionInput.attr('disabled', 'disabled');
             };

         // Hook up the autocompleter before creating the link connection
         $suggestionInput.mozillaAutocomplete({
             minLength: 1,
             requireValidOption: true,
             autocompleteUrl: $('#autosuggestTitleUrl').attr('data-url'),
             _renderItemAsLink: true,
             buildRequestData: function(req) {
                 req.locale = moveLocale;
                 return req;
             },
             onSelect: function(item, isSilent) {
                 $moveSlug.val(item.slug + '/' + specific_slug);
                 if(!isSilent) {
                     onHide();
                 }
             },
             onDeselect: function(item) {
                 $moveSlug.val('');
             }
         });

         // Show the lookup when the link is clicked
         $lookupLink.click(function(e) {
             e.preventDefault();
             // Show the lookup
             $suggestionContainer.addClass('show');
             $suggestionInput[0].disabled = false;
             $suggestionInput[0].focus();
         });

         // Hide lookup when the field is blurred
         $suggestionInput.blur(onHide);

         // Go to link when blured
         $moveSlug.blur(function() {
             $lookupLink.focus();
         });
     }

    $(document).ready(init);

 }(jQuery, gettext));
