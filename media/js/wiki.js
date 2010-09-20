/*
 * wiki.js
 * Scripts for the wiki app.
 */

(function () {
    var OSES = $.parseJSON($('select#os').attr('data-oses')),  // {'mac': true, 'win': true, ...}
        BROWSERS = $.parseJSON($('select#browser').attr('data-browsers')),  // {'fx4': true, ...}
        VERSIONS = $.parseJSON($('select#browser').attr('data-version-groups')),  // {'fx': [[3.4999, '3'], [3.9999, '35']], 'm': [[1.0999, '1'], [1.9999, '11']]}
        MISSING_MSG = $.parseJSON($('#toc').attr('data-missing-msg'));  // l10nized "missing header" message

    function init() {
        $('select.enable-if-js').removeAttr('disabled');

        initPrepopulatedSlugs();
        initReviewModal();
        initForTags();
    }

    // Return the OS that the cookie indicates or, failing that, that appears
    // to be running. Possible values are {mac, win, linux, maemo, android,
    // undefined}. TODO: cookie stuff
    function guessOs() {
        return BrowserDetect.OS;
    }

    // Return the browser and version that the cookie indicates or, failing
    // that, that appears to be running. Possible values resemble {fx4, fx35,
    // m1, m11}. Return undefined if the currently running browser can't be
    // identified. TODO: cookie stuff
    function guessBrowser() {
        var browser = BrowserDetect.browser,
            version = BrowserDetect.version;
        
        if ((browser === undefined) || (version === undefined) || !VERSIONS[browser]) {
            return;
        }
        
        for (var i = 0; i < VERSIONS[browser].length; i++) {
            if (version < VERSIONS[browser][i][0]) {
                return browser + VERSIONS[browser][i][1];
            }
        }
    }

    // Hide/show the proper page sections that are marked with {for} tags as
    // applying to only certain browsers or OSes. Update the table of contents
    // to reflect what was hidden/shown.
    function initForTags() {
        function updateForsAndToc() {
            // Hide and show document sections accordingly:
            showAndHideFors($('select#os').attr('value'),
                            $('select#browser').attr('value'));

            // Update the table of contents in case headers were hidden or shown:
            $('#toc ol').empty().append(filteredToc($('#doc-content')).children());

            return false;
        }

        var $osMenu = $('select#os'),
            $browserMenu = $('select#browser'),
            guess;

        $osMenu.change(updateForsAndToc);
        $browserMenu.change(updateForsAndToc);

        // Select the sniffed or cookied browser or OS if there is one:
        if (guess = guessOs())
            $osMenu.attr('value', guess);
        if (guess = guessBrowser())
            $browserMenu.attr('value', guess);

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
     * Initialize the modal that shows when the reviewer goes to Approve
     * or Reject a revision.
     */
    function initReviewModal() {
        $('#btn-approve').click(function(ev){
            ev.preventDefault();
            openModal('form.accept-form');
        });
        $('#btn-reject').click(function(ev){
            ev.preventDefault();
            openModal('form.reject-form');
        });

        function openModal(selector) {
            var $modal = $(selector).clone();
            $modal.attr('id', 'review-modal')
                  .append('<a href="#close" class="close">&#x2716;</a>');
            $modal.find('a.close, a.cancel').click(closeModal);

            var $overlay = $('<div id="modal-overlay"></div>');

            $('body').append($overlay).append($modal);

            function closeModal(ev) {
                ev.preventDefault();
                $modal.unbind().remove();
                $overlay.unbind().remove();
                delete $modal;
                delete $overlay;
                return false;
            }
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
    // or that {list at least one browser but not the passed-in one}.
    function showAndHideFors(os, browser) {
        $('.for').each(function(index) {
            var osAttrs = {}, browserAttrs = {},
                foundAnyOses = false, foundAnyBrowsers = false,
                $for = $(this);

            // Divide {for} attrs into OSes and browsers:
            $($for.attr('data-for').split(',')).each(function(index) {
                if (OSES.hasOwnProperty(this)) {
                    osAttrs[this] = true;
                    foundAnyOses = true;
                } else if (BROWSERS.hasOwnProperty(this)) {
                    browserAttrs[this] = true;
                    foundAnyBrowsers = true;
                }
            });

            if ((foundAnyOses && !osAttrs.hasOwnProperty(os)) ||
                (foundAnyBrowsers && !browserAttrs.hasOwnProperty(browser)))
                $(this).hide();  // saves original visibility, which is nice
            else
                $(this).show();  // restores original visibility
        });
    }

    $(document).ready(init);

}());

