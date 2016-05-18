(function(win, doc, $) {

    var $compatWrapper = $('.bc-api');
    // show tables
    $compatWrapper.removeClass('hidden');

    // hide old style compat table and any footnotes
    // go back up DOM to find section heading
    var $sectionHead = $compatWrapper.prevAll('h2').first();
    var sectionHeadIsMatch = $sectionHead.filter(function() {
            return $(this).text().match(/(browser )?compat[i|a]bility/i);
    });
    // is it a browser compat section?
    if(sectionHeadIsMatch) {
        // come back down DOM hiding things until we reach the comapt table.
        $sectionHead.nextUntil('.bc-api').hide().addClass('bc-old-hide');
    }

    // Private var to assign IDs to history for accessibility purposes
    var historyCount = 0;

    // The open button template
    var $historyLink = $('<button title="' + gettext('Open implementation notes') + '" class="bc-history-link only-icon" tabindex="-1"><span>' + gettext('Open') + '</span><i class="ic-history" aria-hidden="true"></i></button>');
    // The close button template
    var $historyCloseButton = $('<button class="bc-history-button"><abbr class="only-icon" title="' + gettext('Return to compatibility table.') + '"><span>' + gettext('Close') + '</span><i class="icon-times" aria-hidden="true"></i></abbr></button>');

    var animationProps = {
        duration: 250,
        queue: false,
        easing: 'linear'
    };

    //  Usage: $('.compat-table').mozCompatTable();
    return jQuery.fn.mozCompatTable = function() {

        return $(this).each(function() {

            var $table = $(this);

            // add beta notice & menu
            addBetaNotice($table);

            // Keep track of what may be open within this table
            var $openCell;

            // This limits very quick opening and closing of cells which results in incorrect height counts
            var animating = false;

            var subjectAnimation = $.extend({ complete: function() { animating = false; } }, animationProps);

            // Activate all history cells for keyboard
            $table.find('.bc-has-history').each(function() {
                var historyId = 'bc-history-' + (++historyCount);
                var $td = $(this);
                var $history = $td.find('.bc-history');

                $td.attr({
                    tabIndex: 0,
                    'aria-expanded': false,
                    'aria-controls': historyId
                });

                $history.attr('id', historyId);
                // generate and add button to open history tray
                $historyLink.clone().insertBefore($history);
            });

            // Listen for interaction on "history" cells
            $table.on('click touchend', '.bc-has-history', function(e) {
                var $actualTarget = $(e.target);

                // Don't do open/close if the user interaction within the history section
                if($actualTarget.parents('.bc-history').length || $actualTarget.hasClass('bc-history')) {
                    e.stopImmediatePropagation();
                    return;
                }

                // don't also click if this was a touch
                e.preventDefault();

                // Close previous cell, open the next one
                closeAndOpenHistory($(this));
            });

            // Listen for interaction on "close" buttons
            $table.on('click touchend', '.bc-history-button', function(ev) {
                ev.stopImmediatePropagation();
                hideHistory();
            });

            // Listen for keys to open/close history
            $table.on('keypress', '.bc-has-history', function(ev) {
                var $td = $(this);
                var key = ev.which;

                if(key === 13 || key === 32) {
                    closeAndOpenHistory($td);
                    ev.preventDefault();
                } else if(key === 27) {
                    hideHistory();
                    ev.preventDefault();
                }
            });

            // add beta notice & associated functonality
            function addBetaNotice($table) {
                var $betaMenuWrapper = $('<div />', { 'class': 'bc-beta-menu' });
                var $betaMenuTrigger = $('<a />', { text: gettext('New compatibility tables are in beta '), href: '/en-US/docs/New_Compatibility_Tables_Beta' }).append($('<i>', { class: 'icon-caret-down', 'aria-hidden': 'true' }));
                var $betaSubmenu = $('<ul />', { 'class': 'submenu js-submenu' });
                var betaSubmenuItems = [];

                var $betaLink = $('<a />', { text: gettext('More about the beta.'), href: '/en-US/docs/New_Compatibility_Tables_Beta' });
                betaSubmenuItems.push($betaLink);

                var $betaSurvey = $('<a />', { text: gettext('Take the survey'), href: 'http://www.surveygizmo.com/s3/2342437/0b5ff6b6b8f6', 'class': 'external external-icon' });
                betaSubmenuItems.push($betaSurvey);

                var $betaError = $('<button />', { text: gettext('Report an error.'), 'class': 'button bc-error' });
                $betaError.on('click', function(){
                    mdn.analytics.trackEvent({
                        category: 'Compat Tables Error',
                        action: location.pathname
                    });
                    mdn.Notifier.growl(gettext('Reported. Thanks!'), { duration: 2000, closable: true }).success();
                });
                betaSubmenuItems.push($betaError);

                var $betaShowOld = $('<button />', { text: gettext('Show old table.'), 'class': 'button bc-old' });
                $betaShowOld.on('click', function(){
                    $('.bc-old-hide').toggle();
                });
                betaSubmenuItems.push($betaShowOld);

                $(betaSubmenuItems).each(function(){
                    var $newItem = $('<li />');
                    $newItem.append(this);
                    $newItem.appendTo($betaSubmenu);
                });

                $betaMenuWrapper.append($betaMenuTrigger).append($betaSubmenu);
                $betaMenuWrapper.insertBefore($table);

                $betaMenuWrapper.mozMenu().mozKeyboardNav();
            }

            // Function which closes any open history, opens the target history
            // Acts as the "router" for open and close directives
            function closeAndOpenHistory($td) {
                if(animating) {
                    return;
                }

                // If no cell is open at the moment, skip the "close" step and just open it
                if(!$openCell) {
                    return _open($td);
                }

                // If they clicks the same cell (are closing), we can leave now
                var previousOpenCell = $openCell && $openCell.get(0);
                if($td.get(0) === previousOpenCell) {
                    $td = null;
                }

                // Close what's open, if anything, and open if $td has a value
                hideHistory($td);
            }

            // Opens the history for a given item
            function showHistory() {
                if(animating) {
                    return;
                }

                var $row = $openCell.closest('tr');
                var $history = $openCell.find('.bc-history').outerWidth($table.width());

                // get cell coords
                var cellLeft = $openCell.offset().left;

                // get cell left border
                var cellLeftBorder = $openCell.css('border-left-width');

                // get table coords
                var tableLeft = $table.offset().left;

                // left coord of table minus left coord of cell
                var historyLeft = tableLeft - cellLeft - parseInt(cellLeftBorder, 10);

                // get cell height
                var cellTop = $openCell.outerHeight();

                // get cell top border
                var celltopBorder = $openCell.css('border-top-width');

                // get cell bottom border
                var cellBottomBorder = $openCell.css('border-bottom-width');

                var historyTop = cellTop - parseInt(cellBottomBorder, 10) - parseInt(celltopBorder, 10);

                var historyHeight;
                var windowWidth;
                var $subject;
                var displayDetect;

                // Add a close button if one doesn't already exist
                if($history.find('.bc-history-button').length === 0) {
                    $historyCloseButton.clone().appendTo($history);
                }

                // move history where it will display
                $history.css({ left: historyLeft, top: historyTop });

                // measure height
                $history.css('display', 'block').attr('aria-hidden', false);
                historyHeight = $history.outerHeight();

                // set max-height to 0 and visibility to visible
                $openCell.addClass('active').attr('aria-expanded', true);

                // add measured height to history and to the cell/row it is being displayed beneath (CSS handles transition)
                displayDetect = $table.find('thead td').first().css('z-index');

                if(displayDetect == 1 ) {
                    $subject = $row.find('td');
                } else if(displayDetect == 2) {
                    $subject = $openCell;
                } else {
                    $subject = $row.find('th, td');
                }

                animating = true;
                $history.css('height', 0).stop().animate({ height: historyHeight }, animationProps);

                $subject.stop().animate({ borderBottomWidth: historyHeight }, subjectAnimation);
            }

            // Hides the history dropdown for a given cell
            function hideHistory($td) {
                var $history, $delayCloseCell;

                if(animating) {
                    return;
                }

                // Animate the borders back down
                $openCell.attr('aria-expanded', false).stop().animate({ borderBottomWidth: '' }, animationProps);
                $openCell.closest('tr').find('th, td').stop().animate({ borderBottomWidth: '' }, animationProps);

                $history = $openCell.find('.bc-history');

                var historyAnimationProps = $.extend({
                    complete: function() {
                        $openCell.removeClass('active');
                        $history.css('display', 'none').css('height', 'auto');
                        $openCell = null;

                        if($td) {
                            _open($td);
                        }
                    }
                }, animationProps);

                $history.attr('aria-hidden', true).stop().animate({ height: '' }, historyAnimationProps);

                // if the focus is inside the .bc-history and we'd lose our keyboard place, move focus to parent
                if($.contains($openCell.get(0), doc.activeElement)) {
                    $openCell.focus();
                }
            }

            // Opens a cell and records it
            function _open($td) {
                // Set this cell as open
                $openCell = $td;
                // Show!
                showHistory();
            }
        });
    };

})(window, document, jQuery);
