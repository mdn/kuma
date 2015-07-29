(function(win, doc, $) {

    // Private var to assign IDs to history for accessibility purposes
    var historyCount = 0;

    // The close button template
    var $historyCloseButton = $('<button class="bc-history-button"><abbr class="only-icon" title="' + gettext('Return to compatability table.') + '"><span>' + gettext('Close') + '</span><i class="icon-times" aria-hidden="true"></i></abbr></button>');

    var animationDuration = 200;

    //  Usage: $('.compat-table').mozCompatTable();
    return jQuery.fn.mozCompatTable = function() {

        return $(this).each(function() {

            var $table = $(this);

            // Keep track of what may be open within this table
            var $openCell;

            // This limits very quick opening and closing of cells which results in incorrect height counts
            var animating = false;

            // Activate all history cells for keyboard;  TODO:  add "aria-controls"
            $table.find('.bc-has-history').each(function() {
                var historyId = 'bc-history-' + (++historyCount);
                var $td = $(this);

                $td.attr({
                    tabIndex: 0,
                    'aria-expanded': false,
                    'aria-controls': historyId
                });
                $td.find('.bc-history').attr('id', historyId);
                $td.find('.bc-history-link').attr('tabIndex', -1);
            });

            // Listen for clicks on "history" cells
            $table.on('click', '.bc-has-history', function(e) {
                var $actualTarget = $(e.target);

                // Don't do open/close if the user clicks within the history section
                if($actualTarget.parents('.bc-history').length || $actualTarget.hasClass('bc-history')) {
                    e.stopImmediatePropagation();
                    return;
                }

                // Close previous cell, open the next one
                closeAndOpenHistory($(this));
            });

            // Listen for clicks on "close" buttons
            $table.on('click', '.bc-history-button', function(ev) {
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
                var historyLeft = tableLeft - cellLeft - parseInt(cellLeftBorder, 10) - 1;

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
                windowWidth = win.innerWidth;
                if(windowWidth > 801) {
                    $subject = $row.find('th, td');
                } else if(windowWidth > 481) {
                    $subject = $row.find('td');
                } else {
                    $subject = $openCell;
                }

                animating = true;
                $history.css('height', 0).stop().animate({ height: historyHeight }, animationDuration);
                $subject.stop().animate({ borderBottomWidth: historyHeight }, animationDuration, function() {
                    animating = false;
                });
            }

            // Hides the history dropdown for a given cell
            function hideHistory($td) {
                var $history, $delayCloseCell;

                if(animating) {
                    return;
                }

                // Animate the borders back down
                $openCell.attr('aria-expanded', false).stop().animate({ borderBottomWidth: '' }, animationDuration);
                $openCell.closest('tr').find('th, td').stop().animate({ borderBottomWidth: '' }, animationDuration);

                $history = $openCell.find('.bc-history');
                $history.attr('aria-hidden', true).stop().animate({ height: '' }, animationDuration, function() {
                    $openCell.removeClass('active');
                    $history.css('display', 'none').css('height', 'auto');
                    $openCell = null;

                    if($td) {
                        _open($td);
                    }
                });

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
