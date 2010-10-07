/*
 * wiki.js
 * Scripts for the wiki app.
 */

(function () {
    var OSES, BROWSERS, VERSIONS, MISSING_MSG;

    function init() {
        $('select.enable-if-js').removeAttr('disabled');

        initPrepopulatedSlugs();
        initActionModals();
        if ($('body').is('.document')) { // Document page
            initForTags();
        }
        if ($('body').is('.translate')) { // Translate page
            initChangeTranslateLocale();
        }
        if ($('body').is('.edit, .new, .translate')) {
            initArticlePreview();
        }

        Marky.createFullToolbar('.forum-editor-tools', '#id_content');
    }

    // Return the OS that the cookie indicates or, failing that, that appears
    // to be running. Possible values are {mac, win, linux, maemo, android,
    // undefined}.
    function initialOs() {
        return $.cookie('for_os') || BrowserDetect.OS;
    }

    // Return the browser and version that the cookie indicates or, failing
    // that, that appears to be running. Possible values resemble {fx4, fx35,
    // m1, m11}. Return undefined if the currently running browser can't be
    // identified.
    function initialBrowser() {
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
        return $.cookie('for_browser') || getVersionGroup(BrowserDetect.browser, BrowserDetect.version);
    }

    // Hide/show the proper page sections that are marked with {for} tags as
    // applying to only certain browsers or OSes. Update the table of contents
    // to reflect what was hidden/shown.
    function initForTags() {

        OSES = $.parseJSON($('select#os').attr('data-oses'));  // {'mac': true, 'win': true, ...}
        BROWSERS = $.parseJSON($('select#browser').attr('data-browsers'));  // {'fx4': true, ...}
        VERSIONS = $.parseJSON($('select#browser').attr('data-version-groups'));  // {'fx': [[3.4999, '3'], [3.9999, '35']], 'm': [[1.0999, '1'], [1.9999, '11']]}
        MISSING_MSG = $.parseJSON($('#toc').attr('data-missing-msg'));  // l10nized "missing header" message

        function updateForsAndToc() {
            // Hide and show document sections accordingly:
            showAndHideFors($('select#os').attr('value'),
                            $('select#browser').attr('value'));

            // Update the table of contents in case headers were hidden or shown:
            $('#toc ol').empty().append(filteredToc($('#doc-content')).children());

            return false;
        }

        function makeMenuChangeHandler(cookieName) {
            function handler() {
                $.cookie(cookieName, $(this).attr('value'), {path: '/'});
                updateForsAndToc();
            }
            return handler;
        }

        var $osMenu = $('select#os'),
            $browserMenu = $('select#browser'),
            initial;

        $osMenu.change(makeMenuChangeHandler('for_os'));
        $browserMenu.change(makeMenuChangeHandler('for_browser'));

        // Select the sniffed or cookied browser or OS if there is one:
        if (initial = initialOs())
            $osMenu.attr('value', initial);  // does not fire change event
        if (initial = initialBrowser())
            $browserMenu.attr('value', initial);

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
        }, field = null;

        for (i in fields) {
            field = fields[i];
            $('#id_slug').addClass('prepopulated_field');
            $(field.id).data('dependency_list', field['dependency_list'])
                   .prepopulate($(field['dependency_ids'].join(',')),
                                field.maxLength);
        };
    }

    /*
     * Initialize modals that activate on the click of elements with
     * class="activates-modal". The activation element is required to
     * have a data-modal-selector attribute that is a CSS selector
     * to the modal to activate (by adding CSS class "active").
     *
     * TODO: Check if other areas of the site can use this and, if so,
     * move to the common bundle somewhere.
     */
    function initActionModals() {
        var $modal, $overlay;
        $('.activates-modal').click(function(ev){
            ev.preventDefault();
            $modal = $($(this).attr('data-modal-selector'));
            $overlay = $('<div id="modal-overlay"></div>');
            if (!$modal.data('inited')) {
                $modal.append('<a href="#close" class="close">&#x2716;</a>')
                    .data('inited', true);
                $modal.find('a.close, a.cancel').click(closeModal);
            }

            $modal.addClass('active');
            $('body').append($overlay);

            return false;
        });

        function closeModal(ev) {
            ev.preventDefault();
            $modal.removeClass('active');
            $overlay.remove();
            return false;
        }
    }

    // Return a table of contents (an <ol>) listing the visible headers within
    // elements in the $pageBody set.
    //
    // The highest header level found within $pageBody is considered to be the
    // top of the TOC: if $pageBody has h2s but no h1s, h2s will be used as the
    // first level of the TOC. Missing headers (such as if you follow an h2
    // directly with an h4) are noted prominently so you can fix them.
    function filteredToc($pageBody) {
        function headerLevel(index, hTag) {
            return parseInt(hTag.tagName[1]);
        }

        var $headers = $pageBody.find(':header:not(:hidden)'),  // :hidden is a little overkill, but it's short.
            $root = $('<ol />'),
            $cur_ol = $root,
            ol_level = Math.min.apply(Math, $headers.map(headerLevel).get());

        // For each header in the document, look upward until you hit something that's hidden. If nothing is found, add the header to the TOC.
        $headers.each(function addIfShown(index) {
            var h_level = headerLevel(0, this),
                $h = $(this);

            // If we're too far down the tree, walk up it.
            for (; ol_level > h_level; ol_level--)
                $cur_ol = $cur_ol.parent().closest('ol');

            // If we're too far up the tree, walk down it, create <ol>s until we aren't:
            for (; ol_level < h_level; ol_level++) {
                var $last_li = $cur_ol.children().last();
                if ($last_li.length == 0)
                    $last_li = $('<li />').append($('<em />')
                                                  .text(MISSING_MSG))
                                          .appendTo($cur_ol);
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
            isInverted = forData.substring(0, 4) == 'not ';
            if (isInverted)
                forData = forData.substring(4);  // strip off "not "

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
            if ((shouldHide && !isInverted) || (!shouldHide && isInverted))
                $(this).hide();  // saves original visibility, which is nice but not necessary
            else
                $(this).show();  // restores original visibility
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
                .click(function(ev){
                    $('div.change-locale').removeClass('open');
                });

        // Open the modal on click of the "change" link
        $('div.change-locale a.change').click(function(ev){
            ev.preventDefault()
            $(this).closest('div.change-locale').addClass('open');
            $('body').one('click', function(ev) {
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
            $btn.attr('disabled', 'disabled')
            $.ajax({
                url: $(this).attr('data-preview-url'),
                type: 'POST',
                data: $('#id_content').serialize(),
                dataType: 'html',
                success: function(html) {
                    $('#preview')
                        .html(html)
                        .find('select.enable-if-js').removeAttr('disabled');
                    initForTags();
                    $btn.removeAttr('disabled')
                },
                error: function() {
                    var msg = gettext("There was an error generating the preview.");
                    $('#preview').html(msg);
                    $btn.removeAttr('disabled')
                }
            });

            e.preventDefault();
            return false;
        });
    }

    $(document).ready(init);

}());
