/*
 * wiki.js
 * Scripts for the wiki app.
 */

(function ($) {
    var OSES, BROWSERS, VERSIONS, MISSING_MSG;

    function init() {
        $('select.enable-if-js').removeAttr('disabled');

        initPrepopulatedSlugs();
        initActionModals();
        initDetailsTags();

        if ($('body').is('.document') || $('body').is('.home')) {  // Document page
            initForTags();
            updateShowforSelectors();
            initHelpfulVote();
        }

        if ($('body').is('.translate')) {  // Translate page
            initChangeTranslateLocale();
        }
        if ($('body').is('.edit, .new, .translate')) {
            initArticlePreview();
            initTitleAndSlugCheck();
        }

        Marky.createFullToolbar('.forum-editor-tools', '#id_content');
    }

    // Make <summary> and <details> tags work even if the browser doesn't support them.
    // From http://mathiasbynens.be/notes/html5-details-jquery
    function initDetailsTags() {
        // Note <details> tag support. Modernizr doesn't do this properly as of 1.5; it thinks Firefox 4 can do it, even though the tag has no "open" attr.
        if (!('open' in document.createElement('details'))) {
            document.documentElement.className += ' no-details';
        }

        // Execute the fallback only if there's no native `details` support
        if (!('open' in document.createElement('details'))) {
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

        OSES = $.parseJSON($('select#os').attr('data-oses'));  // {'mac': true, 'win': true, ...}
        BROWSERS = $.parseJSON($('select#browser').attr('data-browsers'));  // {'fx4': true, ...}
        VERSIONS = $.parseJSON($('select#browser').attr('data-version-groups'));  // {'fx': [[3.4999, '3'], [3.9999, '35']], 'm': [[1.0999, '1'], [1.9999, '11']]}
        MISSING_MSG = gettext('[missing header]');

        var $osMenu = $('select#os'),
            $browserMenu = $('select#browser'),
            $origBrowserOptions = $browserMenu.find('option').clone(),
            $body = $('body'),
            hash = hashFragment(),
            isSetManually;

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
                document.location.hash = "os=" + $osMenu.val() + "&browser=" + $browserMenu.val();
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
                          .attr('data-dependency');
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
                    document.location = url.replace('/mobile/', '/home/');
                } else {
                    document.location = url.replace('/home/', '/mobile/');
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
            updateShowforSelectors();
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
                updateShowforSelectors();
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
                    if ($detectedOS.attr('data-dependency') != currentDependency) {
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

    /*
     * Initialize wiki action modals.
     * @see libs/jquery.modal.js
     */
    function initActionModals() {
        $('.activates-modal').initClickModal();
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
            $cur_ol.append($('<li />').text($h.text()).wrapInner($('<a>').attr('href', '#' + $h.attr('id'))));
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
            forData = $(this).attr('data-for');
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
                if (OSES.hasOwnProperty(this)) {
                    osAttrs[this] = true;
                    foundAnyOses = true;
                } else if (BROWSERS.hasOwnProperty(this)) {
                    browserAttrs[this] = true;
                    foundAnyBrowsers = true;
                }
            });

            shouldHide = (foundAnyOses && !osAttrs.hasOwnProperty(os)) ||
                         (foundAnyBrowsers && !browserAttrs.hasOwnProperty(browser));
            if ((shouldHide && !isInverted) || (!shouldHide && isInverted)) {
                $(this).hide();  // saves original visibility, which is nice but not necessary
            }
            else {
                $(this).show();  // restores original visibility
            }
        });
    }

    /*
     * Initialize the Change locale link on the translate page
     */
    function initChangeTranslateLocale() {
        // Add the close button to the modal and handle clicks
        $('#change-locale')
            .append('<a href="#close" class="close">&#x2716;</a>')
            .click(function(ev){
                ev.stopPropagation();
            })
            .find('a.close')
                .click(function(e){
                    $('div.change-locale').removeClass('open');
                    e.preventDefault();
                    return false;
                });

        // Open the modal on click of the "change" link
        $('div.change-locale a.change').click(function(ev){
            ev.preventDefault();
            $(this).closest('div.change-locale').addClass('open');
            $('body').one('click', function() {
                $('div.change-locale').removeClass('open');
            });
            return false;
        });
    }

    /*
     * Initialize the article preview functionality.
     */
    function initArticlePreview() {
        $('#btn-preview').click(function(e) {
            var $btn = $(this);
            $btn.attr('disabled', 'disabled');
            $.ajax({
                url: $(this).attr('data-preview-url'),
                type: 'POST',
                data: $('#id_content').serialize(),
                dataType: 'html',
                success: function(html) {
                    $('#preview')
                        .html(html)
                        .find('select.enable-if-js').removeAttr('disabled');
                    document.location.hash = 'preview';
                    initForTags();
                    updateShowforSelectors();
                    k.initVideo();
                    $btn.removeAttr('disabled');
                },
                error: function() {
                    var msg = gettext('There was an error generating the preview.');
                    $('#preview').html(msg);
                    $btn.removeAttr('disabled');
                }
            });

            e.preventDefault();
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
                url: $form.attr('data-json-url'),
                type: 'GET',
                data: data,
                dataType: 'json',
                success: function(json) {
                    // Success means we found an existing doc
                    var docId = $form.attr('data-document-id');
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

    $(document).ready(init);

}(jQuery));

