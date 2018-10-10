(function ($, win, doc) {
    'use strict';

    var breakpoint = '(min-width: 47.9385em)';
    var $h2s = $('#wikiArticle').find('h2');
    var tocHeight = 0;
    var tocItemHeight = 0;
    var headingMargin = 0;

    /* Mobile
    ************************************************************************ */

    function toggleCollapse(trigger) {
        var $trigger = $(trigger);
        var targetId = $trigger.attr('aria-controls');
        var $target = $('#'+targetId);
        var expanded = $trigger.attr('aria-expanded') === 'true' ? true : false;

        if(expanded) {
            $target.attr('aria-hidden', 'true');
            $trigger.attr('aria-expanded', 'false');
        } else {
            $target.attr('aria-hidden', 'false');
            $trigger.attr('aria-expanded', 'true');
        }
    }

    function collapseHeadings() {
        // don't collapse if just one heading
        if ($h2s.length < 2) {
            return;
        }

        $h2s.each(function(index, h2) {
            var $h2 = $(h2);
            var $buttonTemplate = $('<button class="collapse-trigger" aria-expanded="false" aria-controls="collapse-' + index + '"></button>');
            $buttonTemplate.on('click', function() {
                toggleCollapse(this);
            });
            // add expanded state and buttons to all h2s
            $h2.find('.section-edit').remove();
            // remove inline edit buttons
            $h2.wrapInner($buttonTemplate);
            // wrap all content in a <div> with aria hidden and ID
            $h2.nextUntil('h2').wrapAll('<div id="collapse-' + index + '" class="collapsible" aria-hidden="true"></div>');
        });

        // open by default if user has arrived on specific heading
        if(window.location.hash) {
            var thisHash = window.location.hash;
            var headingId = thisHash.replace(/^#/, '');
            /* must use plain JS to get element, IDs contain characters jQuery can't handle */
            var $heading = $(doc.getElementById(headingId));
            if($heading.length) {
                var $button = $heading.find('button');
                $button.click();
            }
            mdn.utils.scrollToHeading(headingId);
        }
    }


    /* Desktop & Tablet
    ************************************************************************ */

    function stickyToc() {
        // I'm making Table Of Contents lowercase, deal with it

        // detect toc
        var $toc = $('#toc');
        var hasToc = $toc.length ? true : false;
        var underlineTimeOutId;
        var underlineWait = false;
        var underlineWaitTime = 100;
        var wiggleRoom = 20; // vaguely 0.5em, looks right at 100% zoom
        // detect compat table
        var $compatTable = $('.htab');
        var hasCompat = $compatTable.length ? true : false;

        // quit if no #toc on page
        if(!hasToc) {
            return;
        }

        // hide toc if only one heading, unless one is compat link
        if ($h2s.length < 2 && !hasCompat) {
            // hide it
            $toc.addClass('hidden');
            // stop here
            return;
        }

        // set toc height
        tocHeight = $toc.outerHeight();
        tocItemHeight = $toc.find('li:first').outerHeight();


        // In theory we should not have a TOC without any h2s but it doesn't hurt to be careful
        if($h2s.length) {
            // can't use first, it has different margins if it's a :first-child
            var $lastheading = $h2s.last();
            // set headingMargin
            headingMargin = parseInt($lastheading.css('margin-bottom'));
        }

        function underlineCurrent() {
            var screenTop = $(win).scrollTop();
            var screenBottom = screenTop + $(win).height();
            var screenUsableBottom = screenBottom - wiggleRoom;
            var screenUsableTop = screenTop + tocHeight + headingMargin + wiggleRoom;
            var $lastVisible;

            $h2s.each(function(index, h2) {
                var $h2 = $(h2);
                var h2Top = $h2.offset().top;
                var h2Bottom = h2Top + $h2.outerHeight();
                var $linkToH2 = $toc.find('a[href="#' + $h2.attr('id') + '"]');

                // if it's off the top of the usable screen it might be the current section
                if(h2Top < screenUsableTop) {
                    $lastVisible = $linkToH2;
                }

                // if it's in the usable space it's definately current
                if((h2Top > screenUsableTop) && ((h2Bottom + headingMargin) < screenUsableBottom)){
                    // visible
                    $linkToH2.addClass('toc-current');
                } else {
                    $linkToH2.removeClass('toc-current');
                }
            });
            // last visible one is also "current"
            if($lastVisible) {
                $lastVisible.addClass('toc-current');
            }
        }

        // Throttle and debounce underline
        function countDownToUnderline () {
            /* debounce - save underlineWaitTime seconds after scroll stop */
            // clear old countdown to save
            clearTimeout(underlineTimeOutId);
            // begin new countdown to save
            underlineTimeOutId = setTimeout(underlineCurrent, underlineWaitTime);
            /* throttle - save every 500ms */
            if (!underlineWait) {
                // underline current
                underlineCurrent();
                // start wait before saving next time
                underlineWait = true;
                setTimeout(function () {
                    underlineWait = false;
                }, underlineWaitTime);
            }
        }

        function handleTocClick(event) {
            var $thisTarget = $(event.target);
            var $thisLink = $thisTarget.closest('a');
            var linkHref = $thisLink.attr('href');
            var headingId = linkHref.replace(/^#/, '');
            var linkData = {
                category: 'TOC Links',
                action: $thisLink.text(),
                label: linkHref
            };

            // track click
            mdn.analytics.trackLink(event, linkHref, linkData);
            mdn.utils.scrollToHeading(headingId);
        }

        // if 3 lines tall or more make it not sticky
        if (tocHeight > tocItemHeight * 2) {
            $toc.addClass('toc_tall');
            mdn.analytics.trackError('TOC Height Warning', 'Reported height:' + tocHeight);
        }

        // fix scrolling if toc sticky and visible
        if($toc.css('position') === 'sticky' && $toc.is(':visible')) {
            $toc.find('a[href]').on('click', function(event) {
                event.preventDefault();
                handleTocClick(event);
            });
        }

        $(win).on('scroll', function() {
            // underline current section
            countDownToUnderline();
        });
    }

    if(win.matchMedia(breakpoint).matches === true) {
        // don't collapse, possibly make sticky - let stickyToc() figure that out
        stickyToc();
    } else {
        // mobile, collapse
        collapseHeadings();
    }

}(jQuery, window, document));
